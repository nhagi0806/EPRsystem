import EPRsystem3
import SpinFlip2
import time

def main():
    number_of_cycles = 2  # 繰り返し回数

    for _ in range(number_of_cycles):
        EPRsystem3.get_epr_data()
        time.sleep(2)  # 実験間の待機時間
        SpinFlip2.spin_flip()
        time.sleep(2)  # 実験間の待機時間

    print("Experiment sequence completed.")

if __name__ == "__main__":
    main()
