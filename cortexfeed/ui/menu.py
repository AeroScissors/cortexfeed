import threading
import time
from colorama import init, Fore, Style
init(autoreset=True)

BANNER = f"""
{Fore.CYAN}
  ██████╗ ██████╗ ██████╗ ████████╗███████╗██╗  ██╗
 ██╔════╝██╔═══██╗██╔══██╗╚══██╔══╝██╔════╝╚██╗██╔╝
 ██║     ██║   ██║██████╔╝   ██║   █████╗   ╚███╔╝ 
 ██║     ██║   ██║██╔══██╗   ██║   ██╔══╝   ██╔██╗ 
 ╚██████╗╚██████╔╝██║  ██║   ██║   ███████╗██╔╝ ██╗
  ╚═════╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝
{Style.RESET_ALL}
{Fore.WHITE}  local · free · offline — powered by Ollama{Style.RESET_ALL}
"""

MENU = """
{cyan}  [1]{reset} Watch files      — auto-feed changed files to AI
{cyan}  [2]{reset} Run terminal     — run a command, ask AI about output
{cyan}  [3]{reset} AI reads & asks  — dump files, AI decides what it needs
{cyan}  [4]{reset} Chat             — full chat with file/cmd context
{cyan}  [5]{reset} Switch model     — current: {yellow}{model}{reset}
{cyan}  [6]{reset} Prompt builder   — turn your idea into a perfect prompt
{cyan}  [7]{reset} Context mode     — paste conversation, build next prompt
{cyan}  [8]{reset} Investigation    — structured debugging workflow
{cyan}  [9]{reset} Repository Intel — query source code structure
{cyan}  [q]{reset} Quit
"""


def print_banner():
    print(BANNER)


def print_menu(model: str):
    print(MENU.format(
        cyan=Fore.CYAN,
        yellow=Fore.YELLOW,
        reset=Style.RESET_ALL,
        model=model
    ))


def separator(char="─", width=56, color=Fore.CYAN):
    print(color + char * width + Style.RESET_ALL)


def success(msg: str):
    print(Fore.GREEN + msg + Style.RESET_ALL)


def error(msg: str):
    print(Fore.RED + msg + Style.RESET_ALL)


def warning(msg: str):
    print(Fore.YELLOW + msg + Style.RESET_ALL)


def info(msg: str):
    print(Fore.CYAN + msg + Style.RESET_ALL)


def prompt(label: str) -> str:
    return input(Fore.YELLOW + label + Style.RESET_ALL).strip()


def loading(message: str = "Building your prompt"):
    """Animated loading dots — call stop_loading() to stop it."""
    stop_event = threading.Event()

    def animate():
        dots = 0
        while not stop_event.is_set():
            print(f"\r{Fore.CYAN}{message}{'.' * dots}{' ' * (4 - dots)}{Style.RESET_ALL}", end="", flush=True)
            dots = (dots + 1) % 5
            time.sleep(0.4)
        print(f"\r{Fore.GREEN}{message}... done!{Style.RESET_ALL}     ")

    t = threading.Thread(target=animate, daemon=True)
    t.start()
    return stop_event


def stop_loading(stop_event):
    stop_event.set()
    time.sleep(0.5)