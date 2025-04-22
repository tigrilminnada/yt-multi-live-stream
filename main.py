import os
import time
import subprocess
import threading
import json
from datetime import datetime
import platform
import signal
from collections import OrderedDict

class YouTubeMultiStreamer:
    def __init__(self):
        self.accounts = OrderedDict()  # {id: account_data}
        self.next_account_id = 1
        self.stream_processes = {}
        self.presets = {
            'low': {'video': '1500k', 'audio': '128k', 'scale': '854:480', 'fps': 30},
            'medium': {'video': '3000k', 'audio': '128k', 'scale': '1280:720', 'fps': 30},
            'high': {'video': '4500k', 'audio': '192k', 'scale': '1920:1080', 'fps': 30},
            'ultra': {'video': '6000k', 'audio': '256k', 'scale': '2560:1440', 'fps': 60}
        }
        self.current_preset = 'medium'
        self.load_config()
        self.status_refresh_rate = 5  # seconds

    def clear_screen(self):
        """Clear the console screen"""
        if platform.system() == "Windows":
            os.system('cls')
        else:
            os.system('clear')

    def show_banner(self):
        """Display MASANTO banner"""
        banner = """
        ███╗   ███╗ █████╗ ███████╗ █████╗ ███╗   ██╗████████╗ ██████╗ 
        ████╗ ████║██╔══██╗██╔════╝██╔══██╗████╗  ██║╚══██╔══╝██╔═══██╗
        ██╔████╔██║███████║███████╗███████║██╔██╗ ██║   ██║   ██║   ██║
        ██║╚██╔╝██║██╔══██║╚════██║██╔══██║██║╚██╗██║   ██║   ██║   ██║
        ██║ ╚═╝ ██║██║  ██║███████║██║  ██║██║ ╚████║   ██║   ╚██████╔╝
        ╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝    ╚═════╝ 
        
              YouTube Multi-Streaming Tool v3.0 (Windows Edition)
        =================================================================
        |    Seller DO & RDP/VPS Murah https://wa.me/6282323434432      |
        =================================================================
        """
        print(banner)

    def load_config(self):
        """Load configuration from JSON file"""
        try:
            with open('config.json', 'r') as f:
                config = json.load(f, object_pairs_hook=OrderedDict)
                self.accounts = config.get('accounts', OrderedDict())
                self.next_account_id = config.get('next_account_id', 1)
                self.current_preset = config.get('current_preset', 'medium')
                print("Configuration loaded successfully.")
        except (FileNotFoundError, json.JSONDecodeError):
            print("Creating new configuration file...")
            self.save_config()

    def save_config(self):
        """Save configuration to JSON file"""
        with open('config.json', 'w') as f:
            json.dump({
                'accounts': self.accounts,
                'next_account_id': self.next_account_id,
                'current_preset': self.current_preset
            }, f, indent=4)

    def add_account(self, stream_key, video_source='', label=''):
        """Add new streaming account"""
        account_id = self.next_account_id
        self.accounts[account_id] = {
            'id': account_id,
            'stream_key': stream_key,
            'video_source': video_source,
            'preset': self.current_preset,
            'label': label,
            'status': 'stopped',
            'pid': None,
            'start_time': None,
            'last_update': None
        }
        self.next_account_id += 1
        self.save_config()
        return account_id

    def remove_account(self, account_id):
        """Remove streaming account"""
        if account_id in self.accounts:
            if self.accounts[account_id]['status'] == 'streaming':
                self.stop_stream(account_id)
            del self.accounts[account_id]
            self.save_config()
            return True
        return False

    def update_account(self, account_id, **kwargs):
        """Update account properties"""
        if account_id in self.accounts:
            for key, value in kwargs.items():
                if key in self.accounts[account_id]:
                    self.accounts[account_id][key] = value
            self.accounts[account_id]['last_update'] = datetime.now().isoformat()
            self.save_config()
            return True
        return False

    def start_stream(self, account_id, loop=False):
        """Start streaming for an account"""
        if account_id not in self.accounts:
            return False

        account = self.accounts[account_id]
        
        if account['status'] == 'streaming':
            return False

        if not account['video_source']:
            return False

        ffmpeg_cmd = self.build_ffmpeg_command(
            account['video_source'],
            account['stream_key'],
            account['preset']
        )

        def stream_worker(cmd, acc_id, loop_flag):
            while True:
                try:
                    # Start FFmpeg in background
                    if platform.system() == "Windows":
                        startupinfo = subprocess.STARTUPINFO()
                        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                        process = subprocess.Popen(
                            cmd, 
                            shell=True,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            startupinfo=startupinfo
                        )
                    else:
                        process = subprocess.Popen(
                            cmd, 
                            shell=True,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            preexec_fn=os.setsid
                        )

                    # Update account status
                    self.update_account(
                        acc_id,
                        status='streaming',
                        pid=process.pid,
                        start_time=datetime.now().isoformat()
                    )

                    process.wait()  # Wait for process to complete

                    if not loop_flag:
                        break

                    time.sleep(2)  # Delay before restarting
                    
                except Exception as e:
                    print(f"Error in stream worker for account {acc_id}: {str(e)}")
                    break

            # Clean up after streaming stops
            self.update_account(
                acc_id,
                status='stopped',
                pid=None,
                start_time=None
            )

        thread = threading.Thread(
            target=stream_worker,
            args=(ffmpeg_cmd, account_id, loop),
            daemon=True
        )
        thread.start()

        return True

    def stop_stream(self, account_id):
        """Stop streaming for an account"""
        if account_id not in self.accounts:
            return False

        account = self.accounts[account_id]
        
        if account['status'] != 'streaming' or account.get('pid') is None:
            return False

        try:
            pid = account['pid']
            if platform.system() == "Windows":
                os.kill(pid, signal.CTRL_C_EVENT)
            else:
                os.killpg(os.getpgid(pid), signal.SIGTERM)
            
            self.update_account(
                account_id,
                status='stopped',
                pid=None,
                start_time=None
            )
            return True
        except ProcessLookupError:
            self.update_account(
                account_id,
                status='stopped',
                pid=None,
                start_time=None
            )
            return False

    def build_ffmpeg_command(self, video_source, stream_key, preset_name):
        """Build FFmpeg command based on preset"""
        preset = self.presets.get(preset_name, self.presets['medium'])
        
        base_cmd = f"ffmpeg -re -i \"{video_source}\" "
        
        video_settings = (
            f"-c:v libx264 -preset veryfast "
            f"-b:v {preset['video']} -maxrate {preset['video']} "
            f"-bufsize {int(preset['video'].replace('k', '')) * 2}k "
            f"-vf scale={preset['scale']} -g {preset['fps'] * 2} "
            f"-r {preset['fps']} "
            f"-c:a aac -b:a {preset['audio']} -ar 44100"
        )
        
        output = f"-f flv rtmp://a.rtmp.youtube.com/live2/{stream_key}"
        
        return base_cmd + video_settings + " " + output

    def start_all_streams(self, loop=False):
        """Start all streams"""
        for account_id in self.accounts:
            if self.accounts[account_id]['video_source']:
                self.start_stream(account_id, loop)

    def stop_all_streams(self):
        """Stop all streams"""
        for account_id in self.accounts:
            if self.accounts[account_id]['status'] == 'streaming':
                self.stop_stream(account_id)

    def get_stream_status(self, account_id):
        """Get detailed status for a stream"""
        if account_id not in self.accounts:
            return None
            
        account = self.accounts[account_id]
        status = {
            'id': account_id,
            'label': account.get('label', f"Account {account_id}"),
            'status': account['status'],
            'preset': account['preset'],
            'video_source': account['video_source'],
            'stream_key_short': account['stream_key'][:10] + '...' if len(account['stream_key']) > 10 else account['stream_key'],
            'pid': account.get('pid'),
            'uptime': self.calculate_uptime(account.get('start_time'))
        }
        return status

    def calculate_uptime(self, start_time_iso):
        """Calculate uptime from start time"""
        if not start_time_iso:
            return "00:00:00"
            
        start_time = datetime.fromisoformat(start_time_iso)
        uptime = datetime.now() - start_time
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def display_status_dashboard(self):
        """Display real-time streaming status dashboard (without curses)"""
        last_update = time.time()
        
        while True:
            # Clear screen and show banner
            self.clear_screen()
            self.show_banner()
            
            # Display header
            print("\nStreaming Status Dashboard (Auto-refresh every 5 seconds)")
            print("=" * 100)
            print("ID  Label              Preset    Status      Uptime    PID       Video Source")
            print("-" * 100)
            
            # Display each account status
            for account_id in self.accounts:
                status = self.get_stream_status(account_id)
                if not status:
                    continue
                    
                # Highlight running streams
                if status['status'] == 'streaming':
                    status_line = (
                        f"{status['id']:<4} "
                        f"{status['label'][:15].ljust(16)} "
                        f"{status['preset'].ljust(9)} "
                        f"\033[1;32m{status['status'].ljust(11)}\033[0m "
                        f"{status['uptime'].ljust(9)} "
                        f"{str(status.get('pid', 'N/A')).ljust(8)} "
                        f"{status['video_source'][:40]}"
                    )
                else:
                    status_line = (
                        f"{status['id']:<4} "
                        f"{status['label'][:15].ljust(16)} "
                        f"{status['preset'].ljust(9)} "
                        f"\033[1;31m{status['status'].ljust(11)}\033[0m "
                        f"{'00:00:00'.ljust(9)} "
                        f"{'N/A'.ljust(8)} "
                        f"{status['video_source'][:40]}"
                    )
                
                print(status_line)
            
            # Display footer and instructions
            print("-" * 100)
            print("Press Ctrl+C to return to menu (will auto-refresh in 5 seconds)")
            
            # Check for user input (non-blocking)
            try:
                # Wait for 5 seconds or until key press
                start_time = time.time()
                while (time.time() - start_time) < self.status_refresh_rate:
                    if platform.system() == "Windows":
                        # On Windows, use msvcrt for keyboard check
                        import msvcrt
                        if msvcrt.kbhit():
                            msvcrt.getch()  # Clear the input buffer
                            return
                    else:
                        # On Unix, use select for input check
                        import sys
                        import select
                        if select.select([sys.stdin], [], [], 0.1)[0]:
                            sys.stdin.read(1)  # Clear the input buffer
                            return
                    time.sleep(0.1)
                
            except KeyboardInterrupt:
                return

def account_management_menu(streamer):
    """Account management menu"""
    while True:
        streamer.clear_screen()
        streamer.show_banner()
        print("\nAccount Management:")
        print("1. Add New Account")
        print("2. Edit Account")
        print("3. Remove Account")
        print("4. List All Accounts")
        print("5. Back to Main Menu")
        
        choice = input("\nSelect option (1-5): ")
        
        if choice == '1':
            streamer.clear_screen()
            streamer.show_banner()
            print("\nAdd New Streaming Account:")
            stream_key = input("YouTube Stream Key: ")
            video_source = input("Video Source (file path or URL): ")
            label = input("Account Label (optional): ")
            account_id = streamer.add_account(stream_key, video_source, label)
            print(f"\nAccount added successfully with ID: {account_id}")
            input("\nPress Enter to continue...")
            
        elif choice == '2':
            streamer.clear_screen()
            streamer.show_banner()
            print("\nEdit Account:")
            account_id = input("Enter Account ID to edit: ")
            try:
                account_id = int(account_id)
                if account_id in streamer.accounts:
                    account = streamer.accounts[account_id]
                    print(f"\nEditing Account {account_id}: {account.get('label', 'No Label')}")
                    print(f"Current Stream Key: {account['stream_key'][:10]}...")
                    print(f"Current Video Source: {account['video_source']}")
                    print(f"Current Preset: {account['preset']}")
                    
                    new_key = input("\nNew Stream Key (leave blank to keep current): ")
                    new_source = input("New Video Source (leave blank to keep current): ")
                    new_preset = input(f"New Preset ({', '.join(streamer.presets.keys())}, leave blank to keep current): ")
                    
                    updates = {}
                    if new_key:
                        updates['stream_key'] = new_key
                    if new_source:
                        updates['video_source'] = new_source
                    if new_preset and new_preset in streamer.presets:
                        updates['preset'] = new_preset
                    
                    if updates:
                        streamer.update_account(account_id, **updates)
                        print("\nAccount updated successfully!")
                    else:
                        print("\nNo changes made.")
                else:
                    print("\nAccount ID not found.")
            except ValueError:
                print("\nInvalid Account ID. Please enter a number.")
            input("\nPress Enter to continue...")
            
        elif choice == '3':
            streamer.clear_screen()
            streamer.show_banner()
            print("\nRemove Account:")
            account_id = input("Enter Account ID to remove: ")
            try:
                account_id = int(account_id)
                if streamer.remove_account(account_id):
                    print("\nAccount removed successfully!")
                else:
                    print("\nAccount ID not found or could not be removed.")
            except ValueError:
                print("\nInvalid Account ID. Please enter a number.")
            input("\nPress Enter to continue...")
            
        elif choice == '4':
            streamer.clear_screen()
            streamer.show_banner()
            print("\nAll Streaming Accounts:")
            print("-" * 90)
            print("ID  Label              Preset    Status      Video Source")
            print("-" * 90)
            
            for account_id, account in streamer.accounts.items():
                label = account.get('label', 'No Label')[:15].ljust(16)
                preset = account.get('preset', 'medium').ljust(9)
                status = account.get('status', 'stopped').ljust(11)
                video_source = account.get('video_source', 'Not set')[:40]
                
                print(f"{account_id:<4} {label} {preset} {status} {video_source}")
            
            print("-" * 90)
            input("\nPress Enter to continue...")
            
        elif choice == '5':
            break
            
        else:
            print("\nInvalid option. Please try again.")
            time.sleep(1)

def stream_control_menu(streamer):
    """Stream control menu"""
    while True:
        streamer.clear_screen()
        streamer.show_banner()
        print("\nStream Control:")
        print("1. Start Stream for Account")
        print("2. Stop Stream for Account")
        print("3. Start All Streams")
        print("4. Stop All Streams")
        print("5. View Streaming Status")
        print("6. Back to Main Menu")
        
        choice = input("\nSelect option (1-6): ")
        
        if choice == '1':
            streamer.clear_screen()
            streamer.show_banner()
            print("\nStart Stream:")
            account_id = input("Enter Account ID to start: ")
            try:
                account_id = int(account_id)
                if account_id in streamer.accounts:
                    loop = input("Enable looping? (y/n): ").lower() == 'y'
                    if streamer.start_stream(account_id, loop):
                        print("\nStream started successfully!")
                    else:
                        print("\nFailed to start stream. Check if video source is set.")
                else:
                    print("\nAccount ID not found.")
            except ValueError:
                print("\nInvalid Account ID. Please enter a number.")
            input("\nPress Enter to continue...")
            
        elif choice == '2':
            streamer.clear_screen()
            streamer.show_banner()
            print("\nStop Stream:")
            account_id = input("Enter Account ID to stop: ")
            try:
                account_id = int(account_id)
                if streamer.stop_stream(account_id):
                    print("\nStream stopped successfully!")
                else:
                    print("\nNo active stream found for this account.")
            except ValueError:
                print("\nInvalid Account ID. Please enter a number.")
            input("\nPress Enter to continue...")
            
        elif choice == '3':
            streamer.clear_screen()
            streamer.show_banner()
            print("\nStart All Streams:")
            loop = input("Enable looping for all streams? (y/n): ").lower() == 'y'
            streamer.start_all_streams(loop)
            print("\nAttempted to start all streams with video sources set.")
            input("\nPress Enter to continue...")
            
        elif choice == '4':
            streamer.clear_screen()
            streamer.show_banner()
            print("\nStop All Streams:")
            streamer.stop_all_streams()
            print("\nAll streams have been stopped.")
            input("\nPress Enter to continue...")
            
        elif choice == '5':
            try:
                streamer.display_status_dashboard()
            except KeyboardInterrupt:
                print("\nReturning to menu...")
                time.sleep(1)
                
        elif choice == '6':
            break
            
        else:
            print("\nInvalid option. Please try again.")
            time.sleep(1)

def preset_management_menu(streamer):
    """Preset management menu"""
    while True:
        streamer.clear_screen()
        streamer.show_banner()
        print("\nPreset Management:")
        print("1. View All Presets")
        print("2. Set Default Preset")
        print("3. Back to Main Menu")
        
        choice = input("\nSelect option (1-3): ")
        
        if choice == '1':
            streamer.clear_screen()
            streamer.show_banner()
            print("\nAvailable Presets:")
            print("-" * 60)
            print("Name    Video Bitrate Audio Bitrate Resolution FPS")
            print("-" * 60)
            
            for name, settings in streamer.presets.items():
                print(f"{name.ljust(8)} {settings['video'].ljust(13)} {settings['audio'].ljust(13)} "
                      f"{settings['scale'].ljust(11)} {settings['fps']}")
            
            print(f"\nCurrent default preset: {streamer.current_preset}")
            print("-" * 60)
            input("\nPress Enter to continue...")
            
        elif choice == '2':
            streamer.clear_screen()
            streamer.show_banner()
            print("\nSet Default Preset:")
            print(f"Current default: {streamer.current_preset}")
            print("Available presets:", ", ".join(streamer.presets.keys()))
            new_preset = input("\nEnter new default preset: ")
            
            if new_preset in streamer.presets:
                streamer.current_preset = new_preset
                streamer.save_config()
                print(f"\nDefault preset changed to: {new_preset}")
            else:
                print("\nInvalid preset name.")
            input("\nPress Enter to continue...")
            
        elif choice == '3':
            break
            
        else:
            print("\nInvalid option. Please try again.")
            time.sleep(1)

def main():
    streamer = YouTubeMultiStreamer()
    
    while True:
        streamer.clear_screen()
        streamer.show_banner()
        print("\nMain Menu:")
        print("1. Account Management")
        print("2. Stream Control")
        print("3. Preset Management")
        print("4. Exit")
        
        choice = input("\nSelect option (1-4): ")
        
        if choice == '1':
            account_management_menu(streamer)
            
        elif choice == '2':
            stream_control_menu(streamer)
                
        elif choice == '3':
            preset_management_menu(streamer)
            
        elif choice == '4':
            print("\nStopping all streams before exiting...")
            streamer.stop_all_streams()
            print("\nThank you for using MASANTO YouTube Multi-Streaming Tool!")
            break
            
        else:
            print("\nInvalid option. Please try again.")
            time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nProgram interrupted by user. Exiting gracefully...")
    finally:
        # Cleanup if needed
        pass
