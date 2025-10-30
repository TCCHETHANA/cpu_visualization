import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="CPU Scheduling Visualizer", layout="centered")

# --- Navigation Sidebar ---
st.sidebar.title("🔹 Navigation")
page = st.sidebar.radio(
    "Go to", 
    ["🏁 FCFS", "⚡ SJF (Non-Preemptive)", "🥇 Priority Scheduling", "🔁 Round Robin", "📈 Compare All"]
)

st.title("🧠 CPU Scheduling Visualizer")

# --- Common Input Function ---
def get_process_input(include_priority=False):
    st.sidebar.header("Input Process Details")
    num_processes = st.sidebar.number_input("Number of Processes", min_value=1, max_value=10, value=4)

    process_data = []
    for i in range(num_processes):
        st.sidebar.subheader(f"Process {i+1}")
        arrival = st.sidebar.number_input(f"Arrival Time (P{i+1})", min_value=0, value=i)
        burst = st.sidebar.number_input(f"Burst Time (P{i+1})", min_value=1, value=i+2)
        if include_priority:
            priority = st.sidebar.number_input(f"Priority (P{i+1})", min_value=1, value=i+1)
            process_data.append([f"P{i+1}", arrival, burst, priority])
        else:
            process_data.append([f"P{i+1}", arrival, burst])

    columns = ["Process", "Arrival Time", "Burst Time"]
    if include_priority:
        columns.append("Priority")
    df = pd.DataFrame(process_data, columns=columns)
    st.subheader("📋 Process Table")
    st.dataframe(df, hide_index=True)
    return df

# --- FCFS ---
def fcfs_scheduling(df):
    df = df.sort_values(by=["Arrival Time"]).reset_index(drop=True)
    start_time, completion_time, turnaround_time, waiting_time = [], [], [], []
    current_time = 0
    for i in range(len(df)):
        if current_time < df.loc[i, "Arrival Time"]:
            current_time = df.loc[i, "Arrival Time"]
        start_time.append(current_time)
        current_time += df.loc[i, "Burst Time"]
        completion_time.append(current_time)
        turnaround_time.append(completion_time[-1] - df.loc[i, "Arrival Time"])
        waiting_time.append(turnaround_time[-1] - df.loc[i, "Burst Time"])
    df["Start Time"] = start_time
    df["Completion Time"] = completion_time
    df["Turnaround Time"] = turnaround_time
    df["Waiting Time"] = waiting_time
    return df, sum(turnaround_time)/len(df), sum(waiting_time)/len(df)

# --- SJF (Non-Preemptive) ---
def sjf_scheduling(df):
    df = df.sort_values(by=["Arrival Time"]).reset_index(drop=True)
    completed = []
    current_time = 0
    start_time, completion_time, turnaround_time, waiting_time = [], [], [], []
    while len(completed) < len(df):
        available = df[(df["Arrival Time"] <= current_time) & (~df.index.isin(completed))]
        if available.empty:
            current_time += 1
            continue
        idx = available["Burst Time"].idxmin()
        start_time.append(current_time)
        current_time += df.loc[idx, "Burst Time"]
        completion_time.append(current_time)
        turnaround_time.append(current_time - df.loc[idx, "Arrival Time"])
        waiting_time.append(turnaround_time[-1] - df.loc[idx, "Burst Time"])
        completed.append(idx)
    df = df.loc[completed].reset_index(drop=True)
    df["Start Time"] = start_time
    df["Completion Time"] = completion_time
    df["Turnaround Time"] = turnaround_time
    df["Waiting Time"] = waiting_time
    return df, sum(turnaround_time)/len(df), sum(waiting_time)/len(df)

# --- Priority Scheduling ---
def priority_scheduling(df, preemptive=False):
    df = df.sort_values(by=["Arrival Time"]).reset_index(drop=True)
    n = len(df)
    completed = []
    current_time = 0
    start_time = [-1]*n
    completion_time = [0]*n
    remaining_time = df["Burst Time"].tolist()
    gantt = []
    while len(completed) < n:
        available = df[(df["Arrival Time"] <= current_time) & (~df.index.isin(completed))]
        if available.empty:
            current_time += 1
            continue
        idx = available["Priority"].idxmin()
        if preemptive:
            if start_time[idx] == -1:
                start_time[idx] = current_time
            remaining_time[idx] -= 1
            gantt.append((df.loc[idx, "Process"], current_time, current_time+1))
            current_time += 1
            if remaining_time[idx] == 0:
                completion_time[idx] = current_time
                completed.append(idx)
        else:
            if start_time[idx] == -1:
                start_time[idx] = current_time
            gantt.append((df.loc[idx, "Process"], current_time, current_time + df.loc[idx, "Burst Time"]))
            current_time += df.loc[idx, "Burst Time"]
            completion_time[idx] = current_time
            completed.append(idx)
    turnaround_time = [completion_time[i] - df.loc[i, "Arrival Time"] for i in range(n)]
    waiting_time = [turnaround_time[i] - df.loc[i, "Burst Time"] for i in range(n)]
    df["Start Time"] = start_time
    df["Completion Time"] = completion_time
    df["Turnaround Time"] = turnaround_time
    df["Waiting Time"] = waiting_time
    return df, sum(turnaround_time)/n, sum(waiting_time)/n, gantt

# --- Round Robin ---
def round_robin(df, quantum):
    df = df.sort_values(by=["Arrival Time"]).reset_index(drop=True)
    n = len(df)
    remaining_time = df["Burst Time"].tolist()
    completion_time = [0]*n
    waiting_time = [0]*n
    turnaround_time = [0]*n
    current_time = 0
    queue = []
    gantt = []
    arrived = [False]*n

    while True:
        for i in range(n):
            if df.loc[i, "Arrival Time"] <= current_time and not arrived[i]:
                queue.append(i)
                arrived[i] = True

        if not queue:
            if all(rt == 0 for rt in remaining_time):
                break
            current_time += 1
            continue

        idx = queue.pop(0)
        exec_time = min(quantum, remaining_time[idx])
        gantt.append((df.loc[idx, "Process"], current_time, current_time + exec_time))
        current_time += exec_time
        remaining_time[idx] -= exec_time

        for i in range(n):
            if df.loc[i, "Arrival Time"] <= current_time and not arrived[i]:
                queue.append(i)
                arrived[i] = True

        if remaining_time[idx] > 0:
            queue.append(idx)
        else:
            completion_time[idx] = current_time

    for i in range(n):
        turnaround_time[i] = completion_time[i] - df.loc[i, "Arrival Time"]
        waiting_time[i] = turnaround_time[i] - df.loc[i, "Burst Time"]

    df["Completion Time"] = completion_time
    df["Turnaround Time"] = turnaround_time
    df["Waiting Time"] = waiting_time
    avg_tat = sum(turnaround_time) / n
    avg_wt = sum(waiting_time) / n
    return df, avg_tat, avg_wt, gantt

# --- Display Function ---
def display_results(result_df, avg_tat, avg_wt, gantt=None):
    st.subheader("📊 Result Table")
    st.dataframe(result_df, hide_index=True)
    st.markdown(f"**Average Turnaround Time:** {avg_tat:.2f}")
    st.markdown(f"**Average Waiting Time:** {avg_wt:.2f}")

    st.subheader("🕒 Gantt Chart")
    fig, ax = plt.subplots(figsize=(8, 2))
    if gantt:
        for process, start, end in gantt:
            ax.barh("CPU", end - start, left=start, label=process)
            ax.text(start + (end - start)/2, 0, process, ha="center", va="center", color="white", fontweight="bold")
    else:
        for i in range(len(result_df)):
            ax.barh("CPU", result_df["Burst Time"][i],
                    left=result_df["Start Time"][i],
                    label=result_df["Process"][i])
            ax.text(result_df["Start Time"][i] + result_df["Burst Time"][i]/2,
                    0, result_df["Process"][i],
                    ha="center", va="center", color="white", fontweight="bold")
    ax.set_xlabel("Time")
    ax.set_yticks([])
    ax.legend(loc="upper right")
    st.pyplot(fig)

# --- PAGE LOGIC ---
if page == "🏁 FCFS":
    st.header("🏁 First Come First Serve (FCFS)")
    df = get_process_input()
    if st.button("Run FCFS"):
        result_df, avg_tat, avg_wt = fcfs_scheduling(df)
        display_results(result_df, avg_tat, avg_wt)

elif page == "⚡ SJF (Non-Preemptive)":
    st.header("⚡ Shortest Job First (Non-Preemptive)")
    df = get_process_input()
    if st.button("Run SJF"):
        result_df, avg_tat, avg_wt = sjf_scheduling(df)
        display_results(result_df, avg_tat, avg_wt)

elif page == "🥇 Priority Scheduling":
    st.header("🥇 Priority Scheduling")
    df = get_process_input(include_priority=True)
    preemptive = st.radio("Mode", ["Non-Preemptive", "Preemptive"])
    if st.button("Run Priority Scheduling"):
        result_df, avg_tat, avg_wt, gantt = priority_scheduling(df, preemptive == "Preemptive")
        display_results(result_df, avg_tat, avg_wt, gantt)

elif page == "🔁 Round Robin":
    st.header("🔁 Round Robin Scheduling")
    df = get_process_input()
    quantum = st.number_input("Enter Time Quantum", min_value=1, value=2)
    if st.button("Run Round Robin"):
        result_df, avg_tat, avg_wt, gantt = round_robin(df, quantum)
        display_results(result_df, avg_tat, avg_wt, gantt)

elif page == "📈 Compare All":
    st.header("📈 Compare All Algorithms")
    df = get_process_input(include_priority=True)
    quantum = st.number_input("Time Quantum for RR", min_value=1, value=2)

    if st.button("Compare Algorithms"):
        results = []
        # Run all algorithms
        fcfs_df, fcfs_tat, fcfs_wt = fcfs_scheduling(df.copy())
        sjf_df, sjf_tat, sjf_wt = sjf_scheduling(df.copy())
        pr_df, pr_tat, pr_wt, _ = priority_scheduling(df.copy(), preemptive=False)
        rr_df, rr_tat, rr_wt, _ = round_robin(df.copy(), quantum)

        results.append(["FCFS", fcfs_tat, fcfs_wt])
        results.append(["SJF", sjf_tat, sjf_wt])
        results.append(["Priority", pr_tat, pr_wt])
        results.append(["Round Robin", rr_tat, rr_wt])

        result_df = pd.DataFrame(results, columns=["Algorithm", "Avg Turnaround Time", "Avg Waiting Time"])
        st.subheader("📊 Comparison Table")
        st.dataframe(result_df, hide_index=True)

        st.subheader("📉 Comparison Graph")
        fig, ax = plt.subplots()
        ax.bar(result_df["Algorithm"], result_df["Avg Turnaround Time"], label="Avg Turnaround Time")
        ax.bar(result_df["Algorithm"], result_df["Avg Waiting Time"], bottom=result_df["Avg Turnaround Time"], label="Avg Waiting Time")
        ax.set_ylabel("Time")
        ax.set_title("Algorithm Performance Comparison")
        ax.legend()
        st.pyplot(fig)
