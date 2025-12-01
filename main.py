import time
import datetime as dt
import schedule
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import os, sys
import json


class AutoAttender:
    url = "https://portal.dhw.ac.jp/uprx/up/pk/pky501/Pky50101.xhtml"
    user = "AXXDCXXX"
    pw = "xxxxxxxxxx"
    
    json_class = {}
    class_checked = {
        "1": False,
        "2": False,
        "3": False,
        "4": False,
        "5": False,
        "6": False
    }
    
    timebetween = [ # 授業時間帯
        [dt.time(8, 30, 00), dt.time(10, 10, 00)], # 1限
        [dt.time(10, 10, 00), dt.time(11, 50, 00)], # 2限
        [dt.time(12, 30, 00), dt.time(14, 10, 00)], # 3限
        [dt.time(14, 10, 00), dt.time(15, 50, 00)], # 4限
        [dt.time(15, 50, 00), dt.time(17, 30, 00)], # 5限
        [dt.time(17, 30, 00), dt.time(19, 10, 00)], # 6限
    ]
    
    classdefault = {
        "Monday" : {
            "1" : [],
            "2" : [],
            "3" : [],
            "4" : [],
            "5" : [],
            "6" : []
        },
        "Tuesday" : {
            "1" : [],
            "2" : [],
            "3" : [],
            "4" : [],
            "5" : [],
            "6" : []
        },
        "Wednesday" : {
            "1" : [],
            "2" : [],
            "3" : [],
            "4" : [],
            "5" : [],
            "6" : []
        },
        "Thursday" : {
            "1" : [],
            "2" : [],
            "3" : [],
            "4" : [],
            "5" : [],
            "6" : []
        },
        "Friday" : {
            "1" : [],
            "2" : [],
            "3" : [],
            "4" : [],
            "5" : [],
            "6" : []
        },
        "Saturday" : {
            "1" : [],
            "2" : [],
            "3" : [],
            "4" : [],
            "5" : [],
            "6" : []
        }
    }
    
    def __init__(self):
        self.running = True
        self.commands = {
            'attend': self.attend_class,
            'reset_checks': self.reset_class_checks,
            'update': self.load_json_files,
            'stop': self.stop,
            'help': self.show_help,
        }
        
        self.load_json_files()

    def stop(self): # スケジューラ停止
        print("スケジュールを停止します。")
        self.running = False

    def show_help(self): # 利用可能なコマンドを表示
        print("\n=== 利用可能なコマンド ===")
        for cmd in self.commands.keys():
            print(f"  {cmd}")
        print("========================\n")
        
    def reset_class_checks(self): # 授業チェック状態をリセット
        for key in self.class_checked.keys():
            self.class_checked[key] = False
        self.logger("授業チェック状態をリセットしました。")
        
    def logger(self, *message): # ログメッセージ
        datetime = dt.datetime.now()
        with open("log.txt", "a", encoding="utf-8") as f:
            if len(message) == 1:
                f.write(f"{datetime}: {message}\n")
                print(f"{datetime}: {message}")
            else:
                f.write(f"{datetime}: success\n")
            
    def load_json_files(self): # 必要なファイルの存在を確認、なければ作製
        
        self.logfileexist = os.path.exists("log.txt") #logファイルの存在を検証
        self.loginfileexist = os.path.exists("login.json") #login.jsonの存在を検証
        self.classexist = os.path.exists("class.json") #class.jsonの存在を検証
        
        if self.logfileexist: ################## log.txtを開く/作る
            self.logger("log.txt は存在しています。")
        else:
            with open("log.txt", "w", encoding="utf-8") as f:
                f.write("This is log file\n")
                self.logger("log.txt を作製しました。")
                
        if self.loginfileexist: ################## login.jsonを開く/作る
            with open("login.json", "r", encoding="utf-8") as f:
                json_login = json.load(f)
                self.user = json_login["username"]
                self.pw = json_login["password"]
                self.logger("login.json を読み込みました。")
        else:
            with open("login.json", "w", encoding="utf-8") as f:
                json.dump({"username": self.user, "password": self.pw}, f, indent=4)
                self.logger("login.json を作製しました。")
                
        if self.classexist: ################## class.jsonを開く/作る
            with open("class.json", "r", encoding="utf-8") as f:
                self.json_class = json.load(f)
                print(self.json_class)
                self.logger("class.json を読み込みました。")
        else:
            with open("class.json", "w", encoding="utf-8") as f:
                json.dump(self.classdefault, f, indent=4)
                self.logger("class.json を作製しました。")
                
        if not (self.logfileexist and self.loginfileexist and self.classexist):
            self.logger("必要なファイルを作製しました。内容を確認して再度実行してください。")
            sys.exit()
    
    def check_class_exist(self): # 現在の授業が存在するか確認、なければ終了、あれば出席
        nowtime = dt.datetime.now().time()
        class_index = None
        for index, (start, end) in enumerate(self.timebetween): # 現在の授業時間帯を確認
            if start <= nowtime < end:
                class_index = index  # インデックスを返す
        if class_index is None:
            return  # 授業時間外
        elif self.class_checked[str(class_index + 1)]: 
            return # すでに出席済み
        else:
            dayJP = {"Monday": "月曜日", "Tuesday": "火曜日", "Wednesday": "水曜日", "Thursday": "木曜日", "Friday": "金曜日", "Saturday": "土曜日", "Sunday": "日曜日"}
            nowday = dt.datetime.now().strftime("%A")
            if nowday == "Sunday":
                for key in self.class_checked.keys():
                    self.class_checked[key] = True
                self.logger("今日は日曜日です。")
                return
            
            else:
                class_index += 1
                self.logger(f"現在の授業は{dayJP[nowday]} {class_index}限です。")
                if self.json_class[nowday][str(class_index)] == []:
                    self.logger("今日のこの時間は授業がありません。")
                elif not self.json_class[nowday][str(class_index)] == [] and len(self.json_class[nowday][str(class_index)]) < 3:
                    self.logger("今日のこの時間の授業は自動出席対象です。")
                    self.attend_class()
                    
                self.class_checked[str(class_index)] = True # 出席済みにする
        
    def attend_class(self): # 自動出席
        self.driver = webdriver.Chrome()
        self.driver.get(self.url)
        self.driver.maximize_window()
        
        try:
            # user form
            user_form = self.driver.find_element(By.ID, "pmPage:loginForm:userId_input")
            user_form.send_keys(self.user)
            
            # password form
            pw_form = self.driver.find_element(By.ID, "pmPage:loginForm:password")
            
            action = ActionChains(self.driver)
            action.move_to_element(pw_form).click().send_keys(self.pw).perform()
            
            # login button
            loggin_btn = self.driver.find_element(By.ID, "pmPage:loginForm:j_idt38")
            loggin_btn.click()
            
            print(f"Login Success{dt.datetime.now()}")
        
        except Exception as e:
            print(e)
            self.logger(e)
        
        time.sleep(5)
        
        try:
            attend_btn = self.driver.find_element(By.ID, "pmPage:funcForm:j_idt140")
            attend_btn.click()
            print("clicked")
            time.sleep(5)
        except Exception as e:
            print(e)
            self.logger(e)
        else:
            self.logger()
            
        self.driver.quit()

        self.logger(f"自動出席を完了しました。")
    
    def schedule_loop(self): # スケジュール実行ループ
        schedule.every().day.at("08:00").do(self.reset_class_checks) # 毎日8時に授業チェック状態をリセット
        
        schedule.every().day.at("08:35").do(self.check_class_exist)
        schedule.every().day.at("10:15").do(self.check_class_exist)
        schedule.every().day.at("12:35").do(self.check_class_exist)
        schedule.every().day.at("14:15").do(self.check_class_exist)
        schedule.every().day.at("15:55").do(self.check_class_exist)
        schedule.every().day.at("17:35").do(self.check_class_exist)
        while self.running:
            schedule.run_pending()
            time.sleep(1)
            
    def input_loop(self): # コマンド入力ループ
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
            
    def run(self):
        # スケジュール実行用スレッド
        schedule_thread = threading.Thread(target=self.schedule_loop, daemon=True)
        schedule_thread.start()

        # コマンド入力用スレッド
        try:
            self.input_loop()
        except KeyboardInterrupt:
            self.stop()
        
        # スレッドの終了を待つ
        schedule_thread.join(timeout=2)
        print("スケジューラを終了しました。")
        
if __name__ == "__main__":
    scheduler = AutoAttender()
    scheduler.run()  # 5秒ごとにrun()を実行