import os
import sys
import time
import random
import mmap
import struct

# проверка и ввод через консоль
try:
    N = int(input("Введите размер матрицы N: "))
    maxprocs = int(input("Введите максимальное число процессов: "))
except ValueError:
    print("нужно вводить целые числа")
    sys.exit(1)

if N <= 0 or maxprocs <= 0:
    print("числа должны быть больше 0")
    sys.exit(1)

dbl = 8  # размер double в байтах

# генерация матриц
random.seed(12345)
a = [random.random() for _ in range(N * N)]
b = [random.random() for _ in range(N * N)]

# списки для результатов
procs_list = []
time_list = []

# умножение матриц через процессы
for nprocs in range(1, maxprocs + 1):
    elapsed_total = 0.0
    for run in range(3):
        size = N * N * dbl
        mm = mmap.mmap(-1, size, flags=mmap.MAP_SHARED, prot=mmap.PROT_READ | mmap.PROT_WRITE)

        def write_c(i, j, value):
            off = (i * N + j) * dbl
            struct.pack_into('d', mm, off, value)

        t0 = time.perf_counter()
        pids = []

        for p in range(nprocs):
            pid = os.fork()
            if pid == 0:
                # дочерний процесс считает свои строки
                for i in range(p, N, nprocs):
                    row_base = i * N
                    for j in range(N):
                        s = 0.0
                        for k in range(N):
                            s += a[row_base + k] * b[k * N + j]
                        write_c(i, j, s)
                os._exit(0)
            else:
                pids.append(pid)

        # родитель ждёт завершения всех процессов
        for pid in pids:
            os.waitpid(pid, 0)

        t1 = time.perf_counter()
        elapsed_total += (t1 - t0)
        mm.close()

    avg_time = elapsed_total / 3
    procs_list.append(nprocs)
    time_list.append(avg_time)

# вывод таблицы времени
print("\nчисло процессов | среднее время (сек)")
for n, t in zip(procs_list, time_list):
    print(f"{n:>15} | {t:.6f}")

# если есть matplotlib, сохраняем график
try:
    import matplotlib.pyplot as plt
    plt.plot(procs_list, time_list, marker='o', label='процессы')
    plt.xlabel("число процессов")
    plt.ylabel("время, сек")
    plt.title(f"умножение матриц {N}x{N} через процессы")
    plt.grid(True)
    plt.legend()
    plt.savefig("matmul_plot.png")
    print("\nГрафик сохранён в matmul_plot.png")
except ImportError:
    print("\nmatplotlib не найден, график не построен, используйте таблицу выше для анализа.")

# объяснение результатов
print("\nобъяснение результатов:")
print("при малом числе процессов ускорение близко к линейному: каждый процесс получает много работы, переключения контекста минимальны")
print("при большом числе процессов производительность падает: переключение контекста, кэш-промахи, накладные расходы на IPC")
