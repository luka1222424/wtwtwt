"""Reproduce current model and seven figures from pinned derived evidence."""
from pathlib import Path
from collections import Counter
import math
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
DATA = ROOT/"current"
OUT = DATA/"generated"
C = pd.read_csv(ROOT/"data/model_coefficients.csv").set_index("method")
timing = pd.read_csv(DATA/"functional_timing.csv")
B = float(timing.iloc[0].mean_s)
O = float(timing.iloc[2].mean_s)
T = 518400
KINDS = ["stable","fixed90","fixed90_alarm","adaptive"]
LABELS = ["Stable","Fixed 90","Fixed 90 + alarms","Adaptive"]

def simulate(period,kind,horizon=T):
    since=stable=prev=0
    requested=False
    events=[]
    for i in range(math.ceil(horizon/period)):
        t=i*period
        tod=t%86400
        mask=int(kind in ("adaptive","fixed90_alarm") and (28800<=tod<36000 or 64800<=tod<72000))
        since+=1
        stable=0 if mask else min(360,stable+1)
        ext=kind in ("stable","adaptive") and requested and stable>=90
        reason="alarm_new" if mask&~prev else ("scheduled_120m" if ext else "scheduled_30m") if since>=(360 if ext else 90) else None
        if reason:
            events.append((t,reason))
            since=0
            requested=True
        prev=mask
    return pd.DataFrame(events,columns=["time_s","reason"])

def project(c,kind,b=B,o=O):
    ev=simulate(o,kind)
    nb,no,nc=math.ceil(T/b),math.ceil(T/o),math.ceil(T/1800)
    n=len(ev)+1
    counts=Counter(ev.reason)
    net=c.opt_block_J-c.opt_block_s*c.opt_sensor_J/(10+c.overhead_s)
    bb,bs,bc=144*c.base_W,nb*c.base_sensor_J/3600,nc*c.base_camera_J/3600
    ob,os,op=144*c.opt_W,no*c.opt_sensor_J/3600,n*net/3600
    be,oe=bb+bs+bc,ob+os+op
    return dict(scenario=kind,baseline_period_s=b,opt_period_s=o,baseline_samples=nb,opt_samples=no,
        baseline_images=nc,opt_requests=len(ev),opt_blocks_assumed=n,scheduled_30m=counts["scheduled_30m"],
        scheduled_120m=counts["scheduled_120m"],alarm_new=counts["alarm_new"],baseline_bg_Wh=bb,
        baseline_sensor_Wh=bs,baseline_camera_Wh=bc,baseline_Wh=be,opt_bg_Wh=ob,opt_sensor_Wh=os,
        opt_net_Pi_Wh=op,opt_Wh=oe,saved_Wh=be-oe,saved_pct=100*(1-oe/be),net_Pi_J=net),ev

def save(fig,name):
    fig.tight_layout()
    for suffix in ("png","svg"):
        fig.savefig(OUT/(name+"."+suffix),dpi=300,bbox_inches="tight")
    plt.close(fig)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    rows=[]
    timeline={}
    for method,c in C.iterrows():
        for kind in KINDS:
            r,ev=project(c,kind)
            rows.append(dict(method=method,**r))
            if method=="independent":
                timeline[kind]=ev
                pd.testing.assert_frame_equal(ev,pd.read_csv(DATA/f"projected_wake_{kind}.csv"),check_exact=False,rtol=1e-10,atol=1e-10)
                ev.to_csv(OUT/f"projected_wake_{kind}.csv",index=False)
    df=pd.DataFrame(rows)
    pd.testing.assert_frame_equal(df,pd.read_csv(DATA/"projections_updated.csv"),check_exact=False,rtol=1e-10,atol=1e-10)
    df.to_csv(OUT/"projections_updated.csv",index=False)
    p=df[df.method=="independent"].set_index("scenario")
    c=C.loc["independent"]
    assert p.loc["adaptive","opt_blocks_assumed"]==109 and p.loc["fixed90_alarm","opt_blocks_assumed"]==288
    assert abs(project(c,"adaptive",20,20+c.overhead_s)[0]["opt_Wh"]-194.54998149504374)<1e-8
    assert all(p.opt_blocks_assumed==1+p.scheduled_30m+p.scheduled_120m+p.alarm_new)
    variants=[]
    bv=pd.read_csv(ROOT/"data/baseline_method_sensitivity.csv")
    ov=pd.read_csv(ROOT/"data/optimized_coefficients.csv")
    for (half,q),v in bv.groupby(["half_window_s","quiet_phase_fraction"]):
        for _,x in ov.iterrows():
            cc=pd.Series(dict(base_W=v.base_W.mean(),base_sensor_J=v.sensor_J.mean(),base_camera_J=v.camera_J.mean(),opt_W=x.low_W,opt_sensor_J=x.sensor_J,opt_block_J=x.block_J,opt_block_s=x.block_s,overhead_s=x.overhead_s))
            for kind in KINDS:
                r,_=project(cc,kind)
                variants.append(dict(half_window_s=half,quiet_phase_fraction=q,opt_source=x.trace,**r))
    pd.DataFrame(variants).to_csv(OUT/"coefficient_sensitivity.csv",index=False)
    s=[]
    for label,o in [("historical cadence",20+c.overhead_s),("production median",timing.iloc[2].median_s),("bench mean",timing.iloc[1].mean_s),("production mean",O)]:
        for k in KINDS:
            r,_=project(c,k,B,o)
            s.append(dict(timing=label,**r))
    pd.DataFrame(s).to_csv(OUT/"timing_sensitivity.csv",index=False)
    plt.rcParams.update({"font.size":10,"axes.spines.top":False,"axes.spines.right":False})
    fig,ax=plt.subplots(figsize=(7,3));y=np.arange(len(timing))
    ax.hlines(y,timing.min_s,timing.max_s,color="gray",label="Observed min–max")
    ax.scatter(timing.mean_s,y,label="Mean",marker="D");ax.scatter(timing.median_s,y,label="Median",marker="o")
    ax.scatter(timing.p95_lower_order_s,y,label="95th percentile (lower order)",marker="|")
    ax.set(yticks=y,yticklabels=timing.test,xlabel="Consecutive interval (s)",title="Measured sensing cadence");ax.invert_yaxis();ax.legend();ax.grid(axis="x",alpha=.2);save(fig,"fig01_measured_cadence")
    wakes=pd.read_csv(DATA/"measured_wake_events.csv")
    start=pd.Timestamp("2026-11-25T18:23:12.819279Z")
    elapsed=(pd.to_datetime(wakes.host_utc,format="mixed")-start).dt.total_seconds()/60
    fig,ax=plt.subplots(figsize=(8,3));reasons=["alarm_new","scheduled_30m","sensor_fault"]
    for j,r in enumerate(reasons):
        m=wakes.reason==r
        ax.scatter(elapsed[m],[j]*sum(m),label=r)
        for x,seq in zip(elapsed[m],wakes.sequence[m]):
            ax.annotate(str(seq),(x,j),xytext=(4,5),textcoords="offset points",fontsize=8)
    for tm,label in [("2026-11-25T18:29:32.464Z","Initial SSH"),("2026-11-25T19:19:28.672Z","Alarm SSH"),("2026-11-25T19:22:28.697Z","Maintenance")]:
        x=(pd.Timestamp(tm)-start).total_seconds()/60
        ax.scatter(x,-1,marker="s",color="black")
        ax.annotate(label,(x,-1),xytext=(-3,-12),textcoords="offset points",ha="right",fontsize=8)
    ax.set(yticks=[-1,0,1,2],yticklabels=["SSH reachable","New alarm","Scheduled wake","Sensor fault"],xlabel="Elapsed time (min)",title="Measured GPIO and independent SSH events",ylim=(-1.7,2.6));ax.grid(axis="x",alpha=.2);save(fig,"fig02_measured_wake_timeline")
    fig,ax=plt.subplots(figsize=(7.5,3.5));r=p.iloc[0]
    vals=np.array([[r.baseline_bg_Wh,r.baseline_sensor_Wh,r.baseline_camera_Wh]]+[[p.loc[k].opt_bg_Wh,p.loc[k].opt_sensor_Wh,p.loc[k].opt_net_Pi_Wh] for k in KINDS])
    labels=["Baseline","Stable","Fixed 90","Fixed 90\n+ alarms","Adaptive"]
    bot=np.zeros(5)
    for j,label in enumerate(["Background","Sensing","Camera / net Pi"]):
        ax.bar(labels,vals[:,j],bottom=bot,label=label);bot+=vals[:,j]
    for i,v in enumerate(bot):ax.text(i,v+3,f"{v:.2f}",ha="center",fontsize=9)
    ax.set(ylabel="Projected energy (Wh / 144 h)",title="Six-day energy projection",ylim=(0,300));ax.legend(loc="lower left");save(fig,"fig03_projected_energy")
    fig,ax=plt.subplots(figsize=(7,3));h=np.arange(145);sec=h*3600
    ax.plot(h,h*c.base_W+(np.ceil(sec/B)*c.base_sensor_J+np.ceil(sec/1800)*c.base_camera_J)/3600,label="Baseline")
    for k in KINDS:
        n=np.searchsorted(timeline[k].time_s,sec,side="left")+(h>0)
        e=h*c.opt_W+(np.ceil(sec/O)*c.opt_sensor_J+n*p.loc[k].net_Pi_J)/3600
        assert abs(e[-1]-p.loc[k].opt_Wh)<1e-8
        ax.plot(h,e,label=k)
    ax.set(xlabel="Elapsed time (h)",ylabel="Projected cumulative energy (Wh)",title="Modelled accumulation");ax.legend();save(fig,"fig04_cumulative_energy")
    fig,ax=plt.subplots(figsize=(7,3.5));bot=np.zeros(4)
    for key,label in [("scheduled_30m","Scheduled 90"),("scheduled_120m","Scheduled 360"),("alarm_new","New alarm"),("initial","Initial boot")]:
        v=np.ones(4) if key=="initial" else p.loc[KINDS,key].to_numpy()
        ax.bar(labels[1:],v,bottom=bot,label=label);bot+=v
    ax.set(ylabel="Assumed Pi activity blocks",title="Projected activation counts");ax.legend();save(fig,"fig05_activation_counts")
    fig,ax=plt.subplots(figsize=(7,3));k=np.arange(601)
    e=144*c.opt_W+(math.ceil(T/O)*c.opt_sensor_J+k*p.iloc[0].net_Pi_J)/3600
    ax.plot(k,100*(1-e/p.iloc[0].baseline_Wh))
    for name,r in p.iterrows():ax.scatter(r.opt_blocks_assumed,r.saved_pct,label=name)
    ax.set(xlabel="Assumed Pi activity blocks / 144 h",ylabel="Projected saving (%)",title="Activation sensitivity");ax.legend();save(fig,"fig06_activation_sensitivity")
    pi=pd.read_csv(DATA/"measured_pi_cycles.csv")
    fig,ax=plt.subplots(figsize=(7,3));ax.bar(pi.run_order,pi.capture_s,label="Capture");ax.bar(pi.run_order,pi.inference_ms.fillna(0)/1000,bottom=pi.capture_s,label="ONNX inference")
    ax.annotate("Cancelled",(6,pi.capture_s.iloc[-1]+.1),ha="center",fontsize=8)
    ax.set(xlabel="Pi run (log order)",ylabel="Measured duration (s)",title="Measured camera and ONNX operations",ylim=(0,3.6));ax.legend();save(fig,"fig07_measured_pi_operations")
    print(p[["baseline_Wh","opt_Wh","saved_pct","opt_blocks_assumed"]].to_string())

if __name__=="__main__":
    main()
