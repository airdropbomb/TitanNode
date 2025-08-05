from aiohttp import (
    ClientResponseError,
    ClientSession,
    ClientTimeout,
    BasicAuth
)
from aiohttp_socks import ProxyConnector
from fake_useragent import FakeUserAgent
from datetime import datetime
from colorama import *
import asyncio, uuid, time, json, re, os, pytz

wib = pytz.timezone('Asia/Jakarta')

class Titan:
    def __init__(self) -> None:
        self.BASE_API = "https://task.titannet.info/api"
        self.WS_API = "wss://task.titannet.info/api/public/webnodes/ws"
        self.VERSION = "0.0.5"
        self.LANGUAGE = "en"
        self.BASE_HEADERS = {}
        self.WS_HEADERS = {}
        self.proxies = []
        self.proxy_index = 0
        self.account_proxies = {}
        self.password = {}
        self.device_ids = {}
        self.access_tokens = {}
        self.refresh_tokens = {}
        self.expires_times = {}

    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def log(self, message):
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}{message}",
            flush=True
        )

    def welcome(self):
        print(
            f"""
            {Fore.GREEN + Style.BRIGHT}       █████╗ ██████╗ ██████╗     ███╗   ██╗ ██████╗ ██████╗ ███████╗
            {Fore.GREEN + Style.BRIGHT}      ██╔══██╗██╔══██╗██╔══██╗    ████╗  ██║██╔═══██╗██╔══██╗██╔════╝
            {Fore.GREEN + Style.BRIGHT}      ███████║██║  ██║██████╔╝    ██╔██╗ ██║██║   ██║██║  ██║█████╗  
            {Fore.GREEN + Style.BRIGHT}      ██╔══██║██║  ██║██╔══██╗    ██║╚██╗██║██║   ██║██║  ██║██╔══╝  
            {Fore.GREEN + Style.BRIGHT}      ██║  ██║██████╔╝██████╔╝    ██║ ╚████║╚██████╔╝██████╔╝███████╗
            {Fore.GREEN + Style.BRIGHT}      ╚═╝  ╚═╝╚═════╝ ╚═════╝     ╚═╝  ╚═══╝ ╚═════╝ ╚═════╝ ╚══════╝
            {Fore.YELLOW + Style.BRIGHT}      Modified by ADB NODE
            """
        )

    def format_seconds(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
    
    def load_accounts(self):
        filename = "accounts.json"
        try:
            if not os.path.exists(filename):
                self.log(f"{Fore.RED}File {filename} Not Found.{Style.RESET_ALL}")
                return

            with open(filename, 'r') as file:
                data = json.load(file)
                if isinstance(data, list):
                    return data
                return []
        except json.JSONDecodeError:
            return []
    
    async def load_proxies(self, use_proxy_choice: int):
        filename = "proxy.txt"
        try:
            if use_proxy_choice == 1:
                async with ClientSession(timeout=ClientTimeout(total=30)) as session:
                    async with session.get("https://raw.githubusercontent.com/monosans/proxy-list/refs/heads/main/proxies/all.txt") as response:
                        response.raise_for_status()
                        content = await response.text()
                        with open(filename, 'w') as f:
                            f.write(content)
                        self.proxies = [line.strip() for line in content.splitlines() if line.strip()]
            else:
                if not os.path.exists(filename):
                    self.log(f"{Fore.RED + Style.BRIGHT}File {filename} Not Found.{Style.RESET_ALL}")
                    return
                with open(filename, 'r') as f:
                    self.proxies = [line.strip() for line in f.read().splitlines() if line.strip()]
            
            if not self.proxies:
                self.log(f"{Fore.RED + Style.BRIGHT}No Proxies Found.{Style.RESET_ALL}")
                return

            self.log(
                f"{Fore.GREEN + Style.BRIGHT}Proxies Total  : {Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT}{len(self.proxies)}{Style.RESET_ALL}"
            )
        
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}Failed To Load Proxies: {e}{Style.RESET_ALL}")
            self.proxies = []

    def check_proxy_schemes(self, proxies):
        schemes = ["http://", "https://", "socks4://", "socks5://"]
        if any(proxies.startswith(scheme) for scheme in schemes):
            return proxies
        return f"http://{proxies}"

    def get_next_proxy_for_account(self, account):
        if account not in self.account_proxies:
            if not self.proxies:
                return None
            proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
            self.account_proxies[account] = proxy
            self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return self.account_proxies[account]

    def rotate_proxy_for_account(self, account):
        if not self.proxies:
            return None
        proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
        self.account_proxies[account] = proxy
        self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return proxy
    
    def build_proxy_config(self, proxy=None):
        if not proxy:
            return None, None, None

        if proxy.startswith("socks"):
            connector = ProxyConnector.from_url(proxy)
            return connector, None, None

        elif proxy.startswith("http"):
            match = re.match(r"http://(.*?):(.*?)@(.*)", proxy)
            if match:
                username, password, host_port = match.groups()
                clean_url = f"http://{host_port}"
                auth = BasicAuth(username, password)
                return None, clean_url, auth
            else:
                return None, proxy, None

        raise Exception("Unsupported Proxy Type.")
    
    def generate_device_id(self):
        return str(uuid.uuid4())
    
    def mask_account(self, account):
        if "@" in account:
            local, domain = account.split('@', 1)
            mask_account = local[:3] + '*' * 3 + local[-3:]
            return f"{mask_account}@{domain}"
        
        mask_account = account[:3] + '*' * 3 + account[-3:]
        return mask_account

    def print_message(self, account, proxy, device_id: str, color, message):
        self.log(
            f"{Fore.CYAN + Style.BRIGHT}[ Account: {Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT}{self.mask_account(account)}{Style.RESET_ALL}"
            f"{Fore.MAGENTA + Style.BRIGHT} - {Style.RESET_ALL}"
            f"{Fore.CYAN + Style.BRIGHT}Proxy:{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} {proxy} {Style.RESET_ALL}"
            f"{Fore.MAGENTA + Style.BRIGHT}-{Style.RESET_ALL}"
            f"{Fore.CYAN + Style.BRIGHT} Device Id: {Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT}{device_id}{Style.RESET_ALL}"
            f"{Fore.MAGENTA + Style.BRIGHT} - {Style.RESET_ALL}"
            f"{Fore.CYAN + Style.BRIGHT}Status:{Style.RESET_ALL}"
            f"{color + Style.BRIGHT} {message} {Style.RESET_ALL}"
            f"{Fore.CYAN + Style.BRIGHT}]{Style.RESET_ALL}"
        )

    def print_question(self):
        while True:
            try:
                print(f"{Fore.WHITE + Style.BRIGHT}1. Run With Free Proxyscrape Proxy{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}2. Run With Private Proxy{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}3. Run Without Proxy{Style.RESET_ALL}")
                choose = int(input(f"{Fore.BLUE + Style.BRIGHT}Choose [1/2/3] -> {Style.RESET_ALL}").strip())

                if choose in [1, 2, 3]:
                    proxy_type = (
                        "With Free Proxyscrape" if choose == 1 else 
                        "With Private" if choose == 2 else 
                        "Without"
                    )
                    print(f"{Fore.GREEN + Style.BRIGHT}Run {proxy_type} Proxy Selected.{Style.RESET_ALL}")
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Please enter either 1, 2 or 3.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number (1, 2 or 3).{Style.RESET_ALL}")

        rotate = False
        if choose in [1, 2]:
            while True:
                rotate = input(f"{Fore.BLUE + Style.BRIGHT}Rotate Invalid Proxy? [y/n] -> {Style.RESET_ALL}").strip()

                if rotate in ["y", "n"]:
                    rotate = rotate == "y"
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter 'y' or 'n'.{Style.RESET_ALL}")

        return choose, rotate
    
    async def check_connection(self, email: str, proxy_url=None):
        connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
        try:
            async with ClientSession(connector=connector, timeout=ClientTimeout(total=30)) as session:
                async with session.get(url="https://api.ipify.org?format=json", proxy=proxy, proxy_auth=proxy_auth) as response:
                    response.raise_for_status()
                    return True
        except (Exception, ClientResponseError) as e:
            self.print_message(email, proxy_url, self.device_ids[email], Fore.RED, f"Connection Not 200 OK: {Fore.YELLOW + Style.BRIGHT}{str(e)}")
            return None
    
    async def auth_login(self, email: str, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/auth/login"
        data = json.dumps({"password":self.password[email], "user_id":email})
        headers = {
            **self.BASE_HEADERS[email],
            "Content-Length": str(len(data)),
            "Content-Type": "application/json"
        }
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=headers, data=data, proxy=proxy, proxy_auth=proxy_auth) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.print_message(email, proxy_url, self.device_ids[email], Fore.RED, f"Login Failed: {Fore.YELLOW + Style.BRIGHT}{str(e)}")
                return None
    
    async def auth_refresh(self, email: str, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/auth/refresh-token"
        data = json.dumps({"refresh_token":self.refresh_tokens[email]})
        headers = {
            **self.BASE_HEADERS[email],
            "Content-Length": str(len(data)),
            "Content-Type": "application/json"
        }
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=headers, data=data, proxy=proxy, proxy_auth=proxy_auth) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.print_message(email, proxy_url, self.device_ids[email], Fore.RED, f"Refreshing Tokens Failed: {Fore.YELLOW + Style.BRIGHT}{str(e)}")
                return None
    
    async def register_webnodes(self, email: str, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/webnodes/register"
        data = json.dumps({
            "ext_version": self.VERSION,
            "language": self.LANGUAGE,
            "user_script_enabled": True,
            "device_id": self.device_ids[email],
            "install_time": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
        })
        headers = {
            **self.BASE_HEADERS[email],
            "Authorization": f"Bearer {self.access_tokens[email]}",
            "Content-Length": str(len(data)),
            "Content-Type": "application/json"
        }
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=headers, data=data, proxy=proxy, proxy_auth=proxy_auth) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.print_message(email, proxy_url, self.device_ids[email], Fore.RED, f"Registering Webnodes Failed: {Fore.YELLOW + Style.BRIGHT}{str(e)}")
                return None
    
    async def connect_websocket(self, email: str, use_proxy: bool, rotate_proxy: bool):
        wss_url = f"{self.WS_API}?token={self.access_tokens[email]}&device_id={self.device_ids[email]}"
        connected = False

        while True:
            proxy_url = self.get_next_proxy_for_account(email) if use_proxy else None
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            session = ClientSession(connector=connector, timeout=ClientTimeout(total=300))
            try:
                async with session.ws_connect(wss_url, headers=self.WS_HEADERS[email], proxy=proxy, proxy_auth=proxy_auth) as wss:
                    
                    async def send_heartbeat_message():
                        while True:
                            await wss.send_json({
                                "cmd": 1, 
                                "echo": "echo me", 
                                "jobReport": {
                                    "cfgcnt": 2, 
                                    "jobcnt": 0
                                }
                            })
                            self.print_message(email, proxy_url, self.device_ids[email], Fore.BLUE, "Job Reported")
                            await asyncio.sleep(30)

                    if not connected:
                        self.print_message(email, proxy_url, self.device_ids[email], Fore.GREEN, "Websocket Is Connected")
                        connected = True
                        send_ping = asyncio.create_task(send_heartbeat_message())

                    while connected:
                        try:
                            response = await wss.receive_json()
                            if response.get("cmd") == 1:
                                today_point = response.get("userDataUpdate", {}).get("today_points", 0)
                                total_point = response.get("userDataUpdate", {}).get("total_points", 0)

                                self.print_message(email, proxy_url, self.device_ids[email], Fore.GREEN, "User Data Updated "
                                    f"{Fore.MAGENTA + Style.BRIGHT}-{Style.RESET_ALL}"
                                    f"{Fore.CYAN + Style.BRIGHT} Earning: {Style.RESET_ALL}"
                                    f"{Fore.WHITE + Style.BRIGHT}Today {today_point} PTS{Style.RESET_ALL}"
                                    f"{Fore.MAGENTA + Style.BRIGHT} - {Style.RESET_ALL}"
                                    f"{Fore.WHITE + Style.BRIGHT}Total {total_point} PTS{Style.RESET_ALL}"
                                )
                                
                            elif response.get("cmd") == 2:
                                await wss.send_json(response)
                                self.print_message(email, proxy_url, self.device_ids[email], Fore.GREEN, "Echo Me Sent")

                        except Exception as e:
                            self.print_message(email, proxy_url, self.device_ids[email], Fore.YELLOW, f"Websocket Connection Closed: {Fore.RED + Style.BRIGHT}{str(e)}")
                            if send_ping:
                                send_ping.cancel()
                                try:
                                    await send_ping
                                except asyncio.CancelledError:
                                    self.print_message(email, proxy_url, self.device_ids[email], Fore.YELLOW, f"PING Cancelled")

                            await asyncio.sleep(5)
                            connected = False
                            break

            except Exception as e:
                self.print_message(email, proxy_url, self.device_ids[email], Fore.RED, f"Websocket Not Connected: {Fore.YELLOW + Style.BRIGHT}{str(e)}")
                if rotate_proxy:
                    proxy = self.rotate_proxy_for_account(email)

                await asyncio.sleep(5)

            except asyncio.CancelledError:
                self.print_message(email, proxy_url, self.device_ids[email], Fore.YELLOW, "Websocket Closed")
                break
            finally:
                await session.close()

    async def process_check_connection(self, email: str, use_proxy: bool, rotate_proxy: bool):
        while True:
            proxy = self.get_next_proxy_for_account(email) if use_proxy else None

            is_valid = await self.check_connection(email, proxy)
            if is_valid:
                return True
            
            if rotate_proxy:
                proxy = self.rotate_proxy_for_account(email)

            await asyncio.sleep(1)
            continue

    async def process_auth_login(self, email: str, use_proxy: bool, rotate_proxy: bool):
        is_valid = await self.process_check_connection(email, use_proxy, rotate_proxy)
        if is_valid:
            proxy = self.get_next_proxy_for_account(email) if use_proxy else None

            login = await self.auth_login(email, proxy)
            if login and login.get("code") == 0:
                self.access_tokens[email] = login["data"]["access_token"]
                self.refresh_tokens[email] = login["data"]["refresh_token"]
                self.expires_times[email] = login["data"]["expires_at"]

                self.print_message(email, proxy, self.device_ids[email], Fore.GREEN, "Login Success")
                return True
            
            elif login and login.get("code") != 0:
                err_msg = login.get("msg")
                self.print_message(email, proxy, self.device_ids[email], Fore.RED, f"Login Failed: {Fore.YELLOW + Style.BRIGHT}{err_msg}")

            return False
        
    async def process_auth_refresh(self, email: str, use_proxy: bool):
        while True:
            now_time = int(time.time()) + 300
            refresh_at = self.expires_times[email] - now_time
            if refresh_at > 0: await asyncio.sleep(refresh_at)
            else: await asyncio.sleep(5)
            
            proxy = self.get_next_proxy_for_account(email) if use_proxy else None

            refresh = await self.auth_refresh(email, proxy)
            if refresh and refresh.get("code") == 0:
                self.access_tokens[email] = refresh["data"]["access_token"]
                self.refresh_tokens[email] = refresh["data"]["refresh_token"]
                self.expires_times[email] = refresh["data"]["expires_at"]

                self.print_message(email, proxy, self.device_ids[email], Fore.GREEN, "Refreshing Tokens Success")
            
            elif refresh and refresh.get("code") != 0:
                err_msg = refresh.get("msg")
                self.print_message(email, proxy, self.device_ids[email], Fore.RED, f"Refreshing Tokens Failed: {Fore.YELLOW + Style.BRIGHT}{err_msg}")
        
    async def process_register_webnodes(self, email: str, use_proxy: bool):
        proxy = self.get_next_proxy_for_account(email) if use_proxy else None

        register = await self.register_webnodes(email, proxy)
        if register and register.get("code") == 0:

            self.print_message(email, proxy, self.device_ids[email], Fore.GREEN, "Registering Webnodes Success")
            return True
        
        elif register and register.get("code") != 0:
            err_msg = register.get("msg")
            self.print_message(email, proxy, self.device_ids[email], Fore.RED, f"Registering Webnodes Failed: {Fore.YELLOW + Style.BRIGHT}{err_msg}")
        
        return False
        
    async def process_accounts(self, email: str, use_proxy: bool, rotate_proxy: bool):
        logined = await self.process_auth_login(email, use_proxy, rotate_proxy)
        if not logined: return

        registered = await self.process_register_webnodes(email, use_proxy)
        if not registered: return

        await asyncio.gather(*[
            asyncio.create_task(self.process_auth_refresh(email, use_proxy)),
            asyncio.create_task(self.connect_websocket(email, use_proxy, rotate_proxy))
        ])        

    async def main(self):
        try:
            accounts = self.load_accounts()
            if not accounts:
                self.log(f"{Fore.RED + Style.BRIGHT}No Accounts Loaded.{Style.RESET_ALL}")
                return
            
            use_proxy_choice, rotate_proxy = self.print_question()

            use_proxy = False
            if use_proxy_choice in [1, 2]:
                use_proxy = True

            self.clear_terminal()
            self.welcome()
            self.log(
                f"{Fore.GREEN + Style.BRIGHT}Account's Total: {Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT}{len(accounts)}{Style.RESET_ALL}"
            )

            if use_proxy:
                await self.load_proxies(use_proxy_choice)

            self.log(f"{Fore.CYAN + Style.BRIGHT}={Style.RESET_ALL}"*75)

            tasks = []
            for idx, account in enumerate(accounts, start=1):
                if account:
                    email = account["Email"]
                    password = account["Password"]

                    if not "@" in email or not password:
                        self.log(
                            f"{Fore.CYAN + Style.BRIGHT}[ Account: {Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT}{idx}{Style.RESET_ALL}"
                            f"{Fore.MAGENTA + Style.BRIGHT} - {Style.RESET_ALL}"
                            f"{Fore.CYAN + Style.BRIGHT}Status:{Style.RESET_ALL}"
                            f"{Fore.RED + Style.BRIGHT} Invalid Account Data {Style.RESET_ALL}"
                            f"{Fore.CYAN + Style.BRIGHT}]{Style.RESET_ALL}"
                        )
                        continue

                    user_agent =  FakeUserAgent().random
                    
                    self.BASE_HEADERS[email] = {
                        "Accept": "application/json, text/plain, */*",
                        "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
                        "Lang": self.LANGUAGE,
                        "Origin": "https://edge.titannet.info",
                        "Referer": "https://edge.titannet.info/",
                        "Sec-Fetch-Dest": "empty",
                        "Sec-Fetch-Mode": "cors",
                        "Sec-Fetch-Site": "cross-site",
                        "User-Agent": user_agent
                    }
                    
                    self.WS_HEADERS[email] = {
                        "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
                        "Cache-Control": "no-cache",
                        "Connection": "Upgrade",
                        "Host": "task.titannet.info",
                        "Origin": "chrome-extension://flemjfpeajijmofcpgfgckfbmomdflck",
                        "Pragma": "no-cache",
                        "Sec-WebSocket-Extensions": "permessage-deflate; client_max_window_bits",
                        "Sec-WebSocket-Key": "g0PDYtLWQOmaBE5upOBXew==",
                        "Sec-WebSocket-Version": "13",
                        "Upgrade": "websocket",
                        "User-Agent": user_agent
                    }

                    self.password[email] = password
                    self.device_ids[email] = self.generate_device_id()

                    tasks.append(asyncio.create_task(self.process_accounts(email, use_proxy, rotate_proxy)))

            await asyncio.gather(*tasks)

        except Exception as e:
            self.log(f"{Fore.RED+Style.BRIGHT}Error: {e}{Style.RESET_ALL}")
            raise e

if __name__ == "__main__":
    try:
        bot = Titan()
        asyncio.run(bot.main())
    except KeyboardInterrupt:
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{Fore.RED + Style.BRIGHT}[ EXIT ] Titan Node - BOT{Style.RESET_ALL}                                       "                              
        )
