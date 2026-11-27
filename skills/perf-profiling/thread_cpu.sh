#!/usr/bin/env bash
# Usage: thread_cpu.sh <pid> [seconds]
# For each thread of <pid>, over [seconds] (default 3): user and system CPU %,
# run-queue wait % (ready but not running), and context switches per second
# (voluntary: the thread blocked; involuntary: the scheduler took the CPU).
# Needs no root: it reads /proc/<pid>/task/*/{stat,schedstat,status}.
set -euo pipefail
if (( $# < 1 || $# > 2 )) || [[ ! $1 =~ ^[0-9]+$ ]] || [[ ! -d /proc/$1/task ]]; then
  echo "usage: thread_cpu.sh <pid of a running process> [seconds]" >&2
  exit 2
fi
pid=$1
seconds=${2:-3}
hz=$(getconf CLK_TCK)

snapshot() {
  for task in /proc/"$pid"/task/*; do
    [[ -r $task/stat ]] || continue
    # stat fields 14 and 15 are utime and stime; the name is in field 2, in ().
    read -r utime stime < <(sed 's/^.*) //' "$task/stat" | awk '{print $12, $13}')
    read -r _ wait_ns _ < "$task/schedstat"
    vol=$(awk '/^voluntary_ctxt_switches/ {print $2}' "$task/status")
    invol=$(awk '/^nonvoluntary_ctxt_switches/ {print $2}' "$task/status")
    echo "$(basename "$task") $(tr ' ' '_' < "$task/comm") $utime $stime $wait_ns $vol $invol"
  done
}

before=$(snapshot)
sleep "$seconds"
after=$(snapshot)
if [[ -z $after ]]; then
  echo "thread_cpu.sh: process $pid ended during the measurement" >&2
  exit 1
fi
printf '%-8s %-16s %6s %6s %7s %9s %9s\n' tid name user% sys% wait% vol/s invol/s
join <(sort <<< "$before") <(sort <<< "$after") | awk -v hz="$hz" -v s="$seconds" '{
  printf "%-8s %-16s %6.0f %6.0f %7.1f %9.0f %9.0f\n", $1, $2,
    100 * ($9 - $3) / hz / s, 100 * ($10 - $4) / hz / s,
    100 * ($11 - $5) / 1e9 / s, ($12 - $6) / s, ($13 - $7) / s }'
