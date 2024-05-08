import EPRsystem3
import SpinFlip2
import time

def main():
    number_of_cycles = 2  # 1回の実行での繰り返し回数
    cycle_interval = 3600  # 実行間隔（s）

    while True:  # 無限ループを作成して、プログラムを1時間ごとに実行する
        for _ in range(number_of_cycles):
            EPRsystem3.get_epr_data()
            time.sleep(2)  # 実験間の待機時間
            SpinFlip2.spin_flip()
            time.sleep(2)  # 実験間の待機時間
            print("Experiment cycle completed.")
        
        print("Waiting for next cycle...")
        time.sleep(cycle_interval)  # 1時間待つ

if __name__ == "__main__":
    main()