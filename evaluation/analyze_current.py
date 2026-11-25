"""Reproduce final BASELINE vs dynamic HALT-enabled OPTIMIZED comparison."""
from pathlib import Path
from collections import Counter
import math
import re
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parent
DATA=ROOT/"current"
OUT=DATA/"generated"
C=pd.read_csv(ROOT/"data/model_coefficients.csv").set_index("method").loc["independent"]
timing=pd.read_csv(DATA/"functional_timing.csv").set_index("test")
B=float(timing.loc["Baseline","mean_s"])
O=float(timing.loc["Optimized","mean_s"])
T=518400

def simulate(period):
    since=stable=prev=0
    requested=False
    events=[]
    for i in range(math.ceil(T/period)):
        t=i*period
        tod=t%86400
        mask=int(28800<=tod<36000 or 64800<=tod<72000)
        since+=1
        stable=0 if mask else min(360,stable+1)
        ext=requested and stable>=90
        reason="alarm_new" if mask&~prev else ("scheduled_120m" if ext else "scheduled_30m") if since>=(360 if ext else 90) else None
        if reason:
            events.append((t,reason))
            since=0
            requested=True
        prev=mask
    return pd.DataFrame(events,columns=["time_s","reason"])

def project(c=C,b=B,o=O):
    ev=simulate(o)
    nb,no,nc=math.ceil(T/b),math.ceil(T/o),math.ceil(T/1800)
    n=len(ev)+1
    count=Counter(ev.reason)
    net=c.opt_block_J-c.opt_block_s*c.opt_sensor_J/(10+c.overhead_s)
    bb,bs,bc=144*c.base_W,nb*c.base_sensor_J/3600,nc*c.base_camera_J/3600
    ob,os,op=144*c.opt_W,no*c.opt_sensor_J/3600,n*net/3600
    be,oe=bb+bs+bc,ob+os+op
    return dict(method="independent",scenario="adaptive",baseline_period_s=b,opt_period_s=o,baseline_samples=nb,opt_samples=no,
        baseline_images=nc,opt_requests=len(ev),opt_blocks_assumed=n,scheduled_30m=count["scheduled_30m"],
        scheduled_120m=count["scheduled_120m"],alarm_new=count["alarm_new"],baseline_bg_Wh=bb,
        baseline_sensor_Wh=bs,baseline_camera_Wh=bc,baseline_Wh=be,opt_bg_Wh=ob,opt_sensor_Wh=os,
        opt_net_Pi_Wh=op,opt_Wh=oe,saved_Wh=be-oe,saved_pct=100*(1-oe/be),net_Pi_J=net),ev

def save(fig,name):
    fig.tight_layout()
    for ext in ("png","svg","pdf"):
        fig.savefig(OUT/(name+"."+ext),dpi=300,bbox_inches="tight")
    plt.close(fig)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    r,ev=project()
    df=pd.DataFrame([r])
    pd.testing.assert_frame_equal(df,pd.read_csv(DATA/"projections_updated.csv"),check_exact=False,rtol=1e-10,atol=1e-10)
    pd.testing.assert_frame_equal(ev,pd.read_csv(DATA/"projected_wake_adaptive.csv"),check_exact=False,rtol=1e-10,atol=1e-10)
    assert r["opt_blocks_assumed"]==109 and r["alarm_new"]==12
    df.to_csv(OUT/"projections_updated.csv",index=False)
    ev.to_csv(OUT/"projected_wake_adaptive.csv",index=False)
    variants=[]
    bv=pd.read_csv(ROOT/"data/baseline_method_sensitivity.csv")
    ov=pd.read_csv(ROOT/"data/optimized_coefficients.csv")
    for (half,q),v in bv.groupby(["half_window_s","quiet_phase_fraction"]):
        for _,x in ov.iterrows():
            cc=pd.Series(dict(base_W=v.base_W.mean(),base_sensor_J=v.sensor_J.mean(),base_camera_J=v.camera_J.mean(),opt_W=x.low_W,opt_sensor_J=x.sensor_J,opt_block_J=x.block_J,opt_block_s=x.block_s,overhead_s=x.overhead_s))
            rr,_=project(cc)
            variants.append(dict(half_window_s=half,quiet_phase_fraction=q,opt_source=x.trace,**rr))
    pd.DataFrame(variants).to_csv(OUT/"coefficient_sensitivity.csv",index=False)
    plt.rcParams.update({"font.size":10,"axes.spines.top":False,"axes.spines.right":False})
    fig,ax=plt.subplots(figsize=(7,2.6));y=np.arange(2)
    ax.hlines(y,timing.min_s,timing.max_s,color="gray",label="Observed min–max")
    ax.scatter(timing.mean_s,y,label="Mean",marker="D");ax.scatter(timing.median_s,y,label="Median",marker="o")
    ax.scatter(timing.p95_lower_order_s,y,label="95th percentile (lower order)",marker="|")
    ax.set(yticks=y,yticklabels=["BASELINE","OPTIMIZED"],xlabel="Consecutive sample interval (s)",title="Measured sensing cadence");ax.invert_yaxis();ax.legend();ax.grid(axis="x",alpha=.2);save(fig,"fig01_measured_cadence")
    w=pd.read_csv(DATA/"measured_wake_events.csv")
    start=pd.Timestamp("2026-11-25T18:23:12.819279Z")
    elapsed=(pd.to_datetime(w.host_utc,format="mixed")-start).dt.total_seconds()/60
    fig,ax=plt.subplots(figsize=(7,3));reasons=["alarm_new","sensor_fault","scheduled_30m"]
    for j,reason in enumerate(reasons):
        m=w.reason==reason;ax.scatter(elapsed[m],[j]*sum(m))
        for x,seq in zip(elapsed[m],w.sequence[m]):ax.annotate(str(seq),(x,j),xytext=(0,5),textcoords="offset points",ha="center",fontsize=8)
    for line in (DATA/"host_reachability.log").read_text().splitlines():
        match=re.search(r"\[([^]]+)\].*STATE_CHANGE.* -> (UP_SSH22|DOWN_HALT_OR_BOOTING)",line)
        if match:
            x=(pd.Timestamp(match[1])-start).total_seconds()/60
            ax.scatter(x,-1 if match[2]=="UP_SSH22" else -2,marker="o" if match[2]=="UP_SSH22" else "x",color="black")
    ax.set(yticks=[-2,-1,0,1,2],yticklabels=["SSH down","SSH up","New alarm","Sensor fault","Scheduled"],xlabel="Minutes since first optimized sample",title="Measured GPIO and SSH observations");ax.grid(axis="x",alpha=.2);save(fig,"fig02_measured_wake_timeline")
    fig,ax=plt.subplots(figsize=(6,2.8));v=[r["baseline_Wh"],r["opt_Wh"]];bars=ax.barh(["BASELINE","OPTIMIZED"],v);ax.bar_label(bars,fmt="%.2f",padding=3);ax.invert_yaxis();ax.set(xlabel="Projected energy (Wh / 144 h)",xlim=(0,300));ax.grid(axis="x",alpha=.2);save(fig,"fig03_projected_energy")
    fig,ax=plt.subplots(figsize=(7,3));h=np.arange(145);sec=h*3600
    eb=h*C.base_W+(np.ceil(sec/B)*C.base_sensor_J+np.ceil(sec/1800)*C.base_camera_J)/3600
    n=np.searchsorted(ev.time_s,sec,side="left")+(h>0)
    eo=h*C.opt_W+(np.ceil(sec/O)*C.opt_sensor_J+n*r["net_Pi_J"])/3600
    assert abs(eb[-1]-r["baseline_Wh"])<1e-8 and abs(eo[-1]-r["opt_Wh"])<1e-8
    ax.plot(h,eb,label="BASELINE");ax.plot(h,eo,label="OPTIMIZED");ax.set(xlabel="Elapsed time (h)",ylabel="Projected cumulative energy (Wh)");ax.legend();ax.grid(alpha=.2);save(fig,"fig04_cumulative_energy")
    fig,ax=plt.subplots(figsize=(7,3));k=np.arange(601);e=144*C.opt_W+(math.ceil(T/O)*C.opt_sensor_J+k*r["net_Pi_J"])/3600
    ax.plot(k,100*(1-e/r["baseline_Wh"]));ax.scatter([109],[r["saved_pct"]],label="OPTIMIZED workload");ax.set(xlabel="Assumed Pi activity blocks / 144 h",ylabel="Projected saving (%)");ax.legend();save(fig,"fig05_activation_sensitivity")
    pi=pd.read_csv(DATA/"measured_pi_cycles.csv");fig,ax=plt.subplots(figsize=(7,3));ax.bar(pi.run_order,pi.capture_s,label="Capture");ax.bar(pi.run_order,pi.inference_ms.fillna(0)/1000,bottom=pi.capture_s,label="ONNX inference");ax.annotate("Cancelled",(6,pi.capture_s.iloc[-1]+.1),ha="center");ax.set(xlabel="Pi run (log order)",ylabel="Measured duration (s)",ylim=(0,3.6));ax.legend();save(fig,"fig06_measured_pi_operations")
    print(df[["baseline_Wh","opt_Wh","saved_pct","opt_blocks_assumed"]].to_string(index=False))

if __name__=="__main__":
    main()
