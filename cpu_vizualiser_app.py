import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# ----------------------------------------------------------
# Common Input Function
# ----------------------------------------------------------
def get_process_input(include_priority=False, include_quantum=False):
    st.sidebar.header("🧩 Input Process Details")
    num_processes = st.sidebar.number_input("Number of Processes", min_value=1, max_value=10, value=4)
    processes = []
    for i in range(num_processes):
        name = f"P{i+1}"
        arrival = st.sidebar.number_input(f"Arrival Time ({name})", min_value=0, value=i)
        burst = st.sidebar.number_input(f"Burst Time ({name})", min_value=1, value=i+2)
        process = {"name": name, "arrival": arrival, "burst": burst}
        if include_priority:
            process["priority"] = st.sidebar.number_input(f"Priority ({name})", min_value=1, value=i+1)
        processes.append(process)
    quantum = None
    if include_quantum:
        quantum = st.sidebar.number_input("Time Quantum", min_value=1, value=2)
    return processes, quantum


# ----------------------------------------------------------
# FCFS Scheduling
# ----------------------------------------------------------
def fcfs_scheduling(processes):
    processes.sort(key=lambda x: x['arrival'])
    time = 0
    wt, tat = [], []
    gantt = []
    for p in processes:
        start = max(time, p['arrival'])
        finish = start + p['burst']
        time = finish
        wt.append(start - p['arrival'])
        tat.append(finish - p['arrival'])
        gantt.append((p['name'], start, finish))
    avg_wt = sum(wt) / len(wt)
    avg_tat = sum(tat) / len(tat)
    return gantt, wt, tat, avg_wt, avg_tat


# ----------------------------------------------------------
# SJF (Non-Preemptive)
# ----------------------------------------------------------
def sjf_non_preemptive(processes):
    n = len(processes)
    completed, time = 0, 0
    gantt, wt, tat = [], [0]*n, [0]*n
    is_done = [False]*n

    while completed < n:
        idx = -1
        min_burst = float('inf')
        for i in range(n):
            if processes[i]['arrival'] <= time and not is_done[i]:
                if processes[i]['burst'] < min_burst:
                    min_burst = processes[i]['burst']
                    idx = i
        if idx == -1:
            time += 1
            continue

        start = time
        finish = start + processes[idx]['burst']
        time = finish
        wt[idx] = start - processes[idx]['arrival']
        tat[idx] = finish - processes[idx]['arrival']
        gantt.append((processes[idx]['name'], start, finish))
        is_done[idx] = True
        completed += 1

    avg_wt = sum(wt) / n
    avg_tat = sum(tat) / n
    return gantt, wt, tat, avg_wt, avg_tat


# ----------------------------------------------------------
# SRTF (Preemptive)
# ----------------------------------------------------------
def srtf_scheduling(processes):
    n = len(processes)
    remaining = [p['burst'] for p in processes]
    complete = 0
    time = 0
    wt, tat = [0]*n, [0]*n
    exec_log = []

    while complete != n:
        shortest = None
        min_rem = float('inf')
        for i in range(n):
            if processes[i]['arrival'] <= time and remaining[i] > 0:
                if remaining[i] < min_rem:
                    min_rem = remaining[i]
                    shortest = i
        if shortest is None:
            time += 1
            continue

        remaining[shortest] -= 1
        exec_log.append((time, processes[shortest]['name']))
        time += 1

        if remaining[shortest] == 0:
            complete += 1
            finish_time = time
            tat[shortest] = finish_time - processes[shortest]['arrival']
            wt[shortest] = tat[shortest] - processes[shortest]['burst']

    # Merge consecutive entries
    segments = []
    if exec_log:
        seg_start = exec_log[0][0]
        seg_name = exec_log[0][1]
        prev_time = seg_start
        for t, name in exec_log[1:]:
            if name == seg_name and t == prev_time + 1:
                prev_time = t
            else:
                segments.append((seg_name, seg_start, prev_time + 1))
                seg_name, seg_start, prev_time = name, t, t
        segments.append((seg_name, seg_start, prev_time + 1))

    avg_wt = sum(wt) / n
    avg_tat = sum(tat) / n
    return segments, wt, tat, avg_wt, avg_tat


# ----------------------------------------------------------
# Priority Scheduling (Non-Preemptive)
# ----------------------------------------------------------
def priority_scheduling(processes):
    processes.sort(key=lambda x: (x['arrival'], x['priority']))
    time, wt, tat = 0, [], []
    gantt = []

    for p in processes:
        start = max(time, p['arrival'])
        finish = start + p['burst']
        time = finish
        wt.append(start - p['arrival'])
        tat.append(finish - p['arrival'])
        gantt.append((p['name'], start, finish))

    avg_wt = sum(wt) / len(wt)
    avg_tat = sum(tat) / len(tat)
    return gantt, wt, tat, avg_wt, avg_tat


# ----------------------------------------------------------
# Round Robin Scheduling
# ----------------------------------------------------------
def round_robin(processes, quantum):
    n = len(processes)
    remaining = [p['burst'] for p in processes]
    time = 0
    gantt, wt, tat = [], [0]*n, [0]*n
    queue = []
    completed = [False]*n

    while True:
        added = False
        for i in range(n):
            if processes[i]['arrival'] <= time and not completed[i]:
                if i not in queue and remaining[i] > 0:
                    queue.append(i)
        if not queue:
            if all(completed):
                break
            time += 1
            continue

        idx = queue.pop(0)
        added = True
        exec_time = min(quantum, remaining[idx])
        start = time
        finish = start + exec_time
        gantt.append((processes[idx]['name'], start, finish))
        time = finish
        remaining[idx] -= exec_time

        if remaining[idx] == 0:
            completed[idx] = True
            tat[idx] = time - processes[idx]['arrival']
            wt[idx] = tat[idx] - processes[idx]['burst']
        else:
            queue.append(idx)

        if not added:
            time += 1

    avg_wt = sum(wt) / n
    avg_tat = sum(tat) / n
    return gantt, wt, tat, avg_wt, avg_tat


# ----------------------------------------------------------
# Helper to plot Gantt chart
# ----------------------------------------------------------
def plot_gantt(gantt, title):
    fig, ax = plt.subplots(figsize=(10, 2))
    colors = plt.cm.tab20.colors
    for i, (pname, start, end) in enumerate(gantt):
        ax.barh(0, end - start, left=start, color=colors[hash(pname) % len(colors)], edgecolor='black')
        ax.text((start + end) / 2, 0, pname, ha='center', va='center', fontsize=9)
    ax.set_xlabel("Time")
    ax.set_yticks([])
    ax.set_title(title)
    st.pyplot(fig)


# ----------------------------------------------------------
# Streamlit UI
# ----------------------------------------------------------
st.set_page_config(page_title="CPU Scheduling Visualizer", layout="wide")
st.sidebar.title("🧭 Navigation")
page = st.sidebar.radio("Go to", ["🕒 FCFS", "⚡ SJF (Non-Preemptive)", "🚀 SRTF", "🎯 Priority", "🔁 Round Robin"])

st.title("🧮 CPU Scheduling Visualizer")

# ----------------------------------------------------------
# Page Logic
# ----------------------------------------------------------
if page == "🕒 FCFS":
    st.subheader("First Come First Serve (FCFS)")
    processes, _ = get_process_input()
    if st.button("Run FCFS"):
        gantt, wt, tat, avg_wt, avg_tat = fcfs_scheduling(processes)
        df = pd.DataFrame({"Process": [p["name"] for p in processes],
                           "Arrival": [p["arrival"] for p in processes],
                           "Burst": [p["burst"] for p in processes],
                           "Waiting": wt, "Turnaround": tat})
        st.dataframe(df)
        st.success(f"Average Waiting Time: {avg_wt:.2f}")
        st.info(f"Average Turnaround Time: {avg_tat:.2f}")
        plot_gantt(gantt, "FCFS Gantt Chart")

elif page == "⚡ SJF (Non-Preemptive)":
    st.subheader("Shortest Job First (Non-Preemptive)")
    processes, _ = get_process_input()
    if st.button("Run SJF"):
        gantt, wt, tat, avg_wt, avg_tat = sjf_non_preemptive(processes)
        df = pd.DataFrame({"Process": [p["name"] for p in processes],
                           "Arrival": [p["arrival"] for p in processes],
                           "Burst": [p["burst"] for p in processes],
                           "Waiting": wt, "Turnaround": tat})
        st.dataframe(df)
        st.success(f"Average Waiting Time: {avg_wt:.2f}")
        st.info(f"Average Turnaround Time: {avg_tat:.2f}")
        plot_gantt(gantt, "SJF Gantt Chart")

elif page == "🚀 SRTF":
    st.subheader("Shortest Remaining Time First (Preemptive)")
    processes, _ = get_process_input()
    if st.button("Run SRTF"):
        gantt, wt, tat, avg_wt, avg_tat = srtf_scheduling(processes)
        df = pd.DataFrame({"Process": [p["name"] for p in processes],
                           "Arrival": [p["arrival"] for p in processes],
                           "Burst": [p["burst"] for p in processes],
                           "Waiting": wt, "Turnaround": tat})
        st.dataframe(df)
        st.success(f"Average Waiting Time: {avg_wt:.2f}")
        st.info(f"Average Turnaround Time: {avg_tat:.2f}")
        plot_gantt(gantt, "SRTF Gantt Chart")

elif page == "🎯 Priority":
    st.subheader("Priority Scheduling")
    processes, _ = get_process_input(include_priority=True)
    if st.button("Run Priority Scheduling"):
        gantt, wt, tat, avg_wt, avg_tat = priority_scheduling(processes)
        df = pd.DataFrame({"Process": [p["name"] for p in processes],
                           "Arrival": [p["arrival"] for p in processes],
                           "Burst": [p["burst"] for p in processes],
                           "Priority": [p["priority"] for p in processes],
                           "Waiting": wt, "Turnaround": tat})
        st.dataframe(df)
        st.success(f"Average Waiting Time: {avg_wt:.2f}")
        st.info(f"Average Turnaround Time: {avg_tat:.2f}")
        plot_gantt(gantt, "Priority Scheduling Gantt Chart")

elif page == "🔁 Round Robin":
    st.subheader("Round Robin Scheduling")
    processes, quantum = get_process_input(include_quantum=True)
    if st.button("Run Round Robin"):
        gantt, wt, tat, avg_wt, avg_tat = round_robin(processes, quantum)
        df = pd.DataFrame({"Process": [p["name"] for p in processes],
                           "Arrival": [p["arrival"] for p in processes],
                           "Burst": [p["burst"] for p in processes],
                           "Waiting": wt, "Turnaround": tat})
        st.dataframe(df)
        st.success(f"Average Waiting Time: {avg_wt:.2f}")
        st.info(f"Average Turnaround Time: {avg_tat:.2f}")
        plot_gantt(gantt, "Round Robin Gantt Chart")
