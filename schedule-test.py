import schedule
import time
import threading

class TestScheduler:
    def __init__(self):
        self.running = True
        self.commands = {
            'test': self.test,
            'update': self.update,
            'stop': self.stop,
            'help': self.show_help,
        }

    def test(self):
        print("test() executed")

    def update(self):
        print("update() executed")

    def stop(self):
        print("Stopping scheduler...")
        self.running = False

    def show_help(self):
        print("\n=== Available Commands ===")
        for cmd in self.commands.keys():
            print(f"  {cmd}")
        print("========================\n")

    def schedule_loop(self, interval=5):
        schedule.every(interval).seconds.do(self.test)
        while self.running:
            schedule.run_pending()
            time.sleep(1)

    def input_loop(self):
        while self.running:
            try:
                cmd = input(">>> ").strip().lower()
                if cmd in self.commands:
                    self.commands[cmd]()
                elif cmd == '':
                    continue
                else:
                    print(f"Unknown command: '{cmd}'. Type 'help' for available commands.")
            except EOFError:
                break
            except KeyboardInterrupt:
                self.stop()
                break

    def run(self, interval=5):
        # スケジュール実行用スレッド
        schedule_thread = threading.Thread(target=self.schedule_loop, args=(interval,), daemon=True)
        schedule_thread.start()

        # コマンド入力用スレッド
        try:
            self.input_loop()
        except KeyboardInterrupt:
            self.stop()
        
        # スレッドの終了を待つ
        schedule_thread.join(timeout=2)
        print("Scheduler stopped.")

if __name__ == "__main__":
    scheduler = TestScheduler()
    scheduler.run(interval=5)  # 5秒ごとにtest()を実行