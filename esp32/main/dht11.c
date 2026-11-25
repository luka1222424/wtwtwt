#include "dht11.h"

#include <stdbool.h>
#include <string.h>

#include "esp_check.h"
#include "esp_log.h"
#include "esp_rom_sys.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#define DHT11_MIN_INTERVAL_US       2000000LL
#define DHT11_START_LOW_MS          20U
#define DHT11_RELEASE_US            20U
#define DHT11_EDGE_TIMEOUT_US       150U
#define DHT11_ONE_THRESHOLD_US      50U
#define DHT11_MIN_TEMPERATURE_C     0.0f
#define DHT11_MAX_TEMPERATURE_C     50.0f
#define DHT11_MIN_HUMIDITY_PERCENT  20.0f
#define DHT11_MAX_HUMIDITY_PERCENT  90.0f

static const char *TAG = "DHT11";
static gpio_num_t s_data_gpio = GPIO_NUM_NC;
static int64_t s_last_attempt_us;
static portMUX_TYPE s_timing_mux = portMUX_INITIALIZER_UNLOCKED;

/*
 * DHT11 pulse widths are measured by polling because they are only tens of
 * microseconds long. Every loop has a hard deadline, so a disconnected sensor
 * cannot leave the CPU in an unbounded busy wait.
 */
static bool wait_while_level(int level, uint32_t timeout_us,
                             uint32_t *duration_us)
{
    const int64_t started_us = esp_timer_get_time();

    while (gpio_get_level(s_data_gpio) == level) {
        if (esp_timer_get_time() - started_us >= timeout_us) {
            return false;
        }
        esp_rom_delay_us(1);
    }

    if (duration_us != NULL) {
        *duration_us = (uint32_t)(esp_timer_get_time() - started_us);
    }
    return true;
}

static esp_err_t release_data_line(void)
{
    esp_err_t err = gpio_set_direction(s_data_gpio, GPIO_MODE_INPUT_OUTPUT_OD);
    if (err == ESP_OK) {
        err = gpio_set_level(s_data_gpio, 1);
    }
    return err;
}

esp_err_t dht11_init(gpio_num_t gpio_num)
{
    ESP_RETURN_ON_FALSE(GPIO_IS_VALID_OUTPUT_GPIO(gpio_num),
                        ESP_ERR_INVALID_ARG, TAG,
                        "Data GPIO must support both input and output");

    const gpio_config_t config = {
        .pin_bit_mask = 1ULL << gpio_num,
        .mode = GPIO_MODE_INPUT_OUTPUT_OD,
        .pull_up_en = GPIO_PULLUP_ENABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };

    ESP_RETURN_ON_ERROR(gpio_config(&config), TAG,
                        "Could not configure data GPIO");
    ESP_RETURN_ON_ERROR(gpio_set_level(gpio_num, 1), TAG,
                        "Could not release data line");

    s_data_gpio = gpio_num;
    s_last_attempt_us = 0;
    ESP_LOGI(TAG, "Data line ready on GPIO%d with internal pull-up", gpio_num);
    ESP_LOGI(TAG, "Use an external 4.7-10 kOhm pull-up for a bare sensor or unreliable/long wiring");
    return ESP_OK;
}

esp_err_t dht11_read(dht11_reading_t *reading)
{
    ESP_RETURN_ON_FALSE(reading != NULL, ESP_ERR_INVALID_ARG, TAG,
                        "Reading pointer is null");
    ESP_RETURN_ON_FALSE(s_data_gpio != GPIO_NUM_NC,
                        ESP_ERR_INVALID_STATE, TAG,
                        "dht11_init() was not called");
    memset(reading, 0, sizeof(*reading));

    int64_t now_us = esp_timer_get_time();
    if (s_last_attempt_us != 0) {
        const int64_t elapsed_us = now_us - s_last_attempt_us;
        if (elapsed_us < DHT11_MIN_INTERVAL_US) {
            const int64_t remaining_us = DHT11_MIN_INTERVAL_US - elapsed_us;
            const uint32_t remaining_ms =
                (uint32_t)((remaining_us + 999LL) / 1000LL);
            ESP_LOGD(TAG, "Waiting %lu ms for DHT11 minimum interval",
                     (unsigned long)remaining_ms);
            vTaskDelay(pdMS_TO_TICKS(remaining_ms) + 1U);
            now_us = esp_timer_get_time();
        }
    }
    s_last_attempt_us = now_us;

    /* Keep open-drain input+output mode active so the input buffer and pull-up
     * never glitch between releasing the start pulse and sampling the response. */
    esp_err_t err = gpio_set_direction(s_data_gpio, GPIO_MODE_INPUT_OUTPUT_OD);
    if (err != ESP_OK) {
        return err;
    }
    err = gpio_set_level(s_data_gpio, 0);
    if (err != ESP_OK) {
        release_data_line();
        return err;
    }

    /* Host start signal: hold DATA low for at least 18 ms. */
    vTaskDelay(pdMS_TO_TICKS(DHT11_START_LOW_MS) + 1U);

    uint8_t bytes[5] = {0};
    bool timing_ok;

    /*
     * Enter critical section BEFORE releasing DATA high so no tick/ISR can
     * delay detection of the DHT11's 20-40 us response edge.
     */
    taskENTER_CRITICAL(&s_timing_mux);

    gpio_set_level(s_data_gpio, 1);
    esp_rom_delay_us(DHT11_RELEASE_US);

    /* Sensor response: about 80 us low, followed by about 80 us high. */
    timing_ok = wait_while_level(1, DHT11_EDGE_TIMEOUT_US, NULL) &&
                wait_while_level(0, DHT11_EDGE_TIMEOUT_US, NULL) &&
                wait_while_level(1, DHT11_EDGE_TIMEOUT_US, NULL);

    for (int bit = 0; bit < 40 && timing_ok; ++bit) {
        uint32_t high_pulse_us = 0;
        timing_ok = wait_while_level(0, DHT11_EDGE_TIMEOUT_US, NULL) &&
                    wait_while_level(1, DHT11_EDGE_TIMEOUT_US,
                                     &high_pulse_us);
        if (timing_ok && high_pulse_us > DHT11_ONE_THRESHOLD_US) {
            bytes[bit / 8] |= (uint8_t)(1U << (7 - (bit % 8)));
        }
    }

    /* Let the DHT11 finish its ~50 us end-of-frame low pulse cleanly. */
    if (timing_ok) {
        wait_while_level(0, DHT11_EDGE_TIMEOUT_US, NULL);
    }

    taskEXIT_CRITICAL(&s_timing_mux);

    const esp_err_t release_err = release_data_line();
    if (release_err != ESP_OK) {
        return release_err;
    }
    if (!timing_ok) {
        ESP_LOGW(TAG, "Communication timeout while waiting for a sensor pulse");
        return ESP_ERR_TIMEOUT;
    }

    const uint8_t calculated_checksum =
        (uint8_t)(bytes[0] + bytes[1] + bytes[2] + bytes[3]);
    if (calculated_checksum != bytes[4]) {
        ESP_LOGW(TAG,
                 "Checksum mismatch: received=0x%02x calculated=0x%02x",
                 bytes[4], calculated_checksum);
        return ESP_ERR_INVALID_CRC;
    }

    if (bytes[1] > 9U || bytes[3] > 9U) {
        ESP_LOGW(TAG, "Invalid decimal bytes in DHT11 response");
        return ESP_ERR_INVALID_RESPONSE;
    }

    const float humidity = (float)bytes[0] + (float)bytes[1] * 0.1f;
    const float temperature_magnitude =
        (float)(bytes[2] & 0x7fU) + (float)bytes[3] * 0.1f;
    const float temperature =
        (bytes[2] & 0x80U) ? -temperature_magnitude : temperature_magnitude;

    if (temperature < DHT11_MIN_TEMPERATURE_C ||
        temperature > DHT11_MAX_TEMPERATURE_C ||
        humidity < DHT11_MIN_HUMIDITY_PERCENT ||
        humidity > DHT11_MAX_HUMIDITY_PERCENT) {
        ESP_LOGW(TAG, "Out-of-range response: temperature=%.1f C humidity=%.1f %%",
                 (double)temperature, (double)humidity);
        return ESP_ERR_INVALID_RESPONSE;
    }

    reading->temperature_c = temperature;
    reading->humidity_percent = humidity;
    ESP_LOGI(TAG, "Checksum OK");
    return ESP_OK;
}
