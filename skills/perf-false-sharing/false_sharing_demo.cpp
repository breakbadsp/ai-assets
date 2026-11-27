// A known case of false sharing, used to calibrate perf c2c before trusting a
// clean report. Two threads increment two different counters. Without PAD,
// both counters are on one cache line. With -DPAD=1, each has its own line.
#include <atomic>
#include <cstdio>
#include <thread>

#ifndef PAD
#define PAD 0
#endif

struct Counters
{
#if PAD
  alignas(64) std::atomic<unsigned long> first{0};
  alignas(64) std::atomic<unsigned long> second{0};
#else
  std::atomic<unsigned long> first{0};
  std::atomic<unsigned long> second{0};
#endif
};

Counters counters;

int main()
{
  constexpr unsigned long kIterations = 200'000'000;
  std::thread first_writer{[]
                           {
                             for (unsigned long i = 0; i < kIterations; ++i)
                             {
                               counters.first.fetch_add(1, std::memory_order_relaxed);
                             }
                           }};
  std::thread second_writer{[]
                            {
                              for (unsigned long i = 0; i < kIterations; ++i)
                              {
                                counters.second.fetch_add(1, std::memory_order_relaxed);
                              }
                            }};
  first_writer.join();
  second_writer.join();
  std::printf("%lu %lu\n", counters.first.load(), counters.second.load());
}
