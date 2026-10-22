"""
CELESTIAL SCAN v7.0 — Anti-Cheat Screenshare Scanner para Minecraft
Detecta clientes de xit, autoclickers, macros, injetores e bypass de
screenshare. Visual monocromático (preto/branco), scan leve e com poucos falsos positivos.

A logo e as imagens de fundo ficam embutidas neste arquivo (base64),
então o programa funciona mesmo sem internet.

Requisitos:  pip install customtkinter psutil requests pillow
"""
 
import os
import sys
import re
import time
import json
import base64
import queue
import zipfile
import platform
import threading
import subprocess
import webbrowser
from io import BytesIO
from collections import deque
from datetime import datetime, timezone

import tkinter as tk
import tkinter.font as tkfont

import psutil
import requests
import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFilter, ImageTk, ImageOps, ImageEnhance

# ==============================================================================
#                         CONFIGURAÇÕES GERAIS
# ==============================================================================
WEBHOOK_URL = "https://discord.com/api/webhooks/1525195972383346728/JtYsPzaMuVvha-heZ7ptybKuTW__yEI63eF3dSD3xdml7-wua5t1zbgw5KqEKQajPxvO"
DISCORD_LINK = "https://discord.gg/kVcRWRM35m"
APP_NAME = "Celestial Scan"
VERSION = "v7.0"

# ---------------- PALETA — OCEANO PROFUNDO + AZUL NEON -------------------------
BG_DEEP        = "#050505"   # fundo base (preto)
BG_PANEL       = "#0A0A0A"   # sidebar / painéis
BG_CARD        = "#111111"   # cartão escuro
BG_CARD_HOVER  = "#1A1A1A"   # cartão em hover
BORDER_SOFT    = "#232323"
BORDER_STRONG  = "#3A3A3A"

GLASS_HI       = "#1A1A1A"
GLASS_LINE     = "#232323"
BORDER_GLOW    = "#FFFFFF"

TEXT_MAIN      = "#F2F2F2"
TEXT_MUTED     = "#9A9A9A"
TEXT_DIM       = "#5C5C5C"
TEXT_ON_LIGHT  = "#0A0A0A"

BLUE_SHADOW    = "#0A0A0A"
BLUE_DEEP      = "#2A2A2A"
BLUE_MID       = "#7A7A7A"
BLUE_NEON      = "#FFFFFF"
BLUE_BRIGHT    = "#D4D4D4"
BLUE_GLOW      = "#FFFFFF"
CYAN           = "#E6E6E6"

SEV_CRITICAL   = "#FFFFFF"
SEV_HIGH       = "#D0D0D0"
SEV_MEDIUM     = "#A8A8A8"
SEV_LOW        = "#767676"
SEV_OK         = "#E6E6E6"

RED_BG, RED_BD = "#0D0D0D", "#FFFFFF"
GREEN_BG, GREEN_BD = "#BDBDBD", "#D9D9D9"
AMBER_BG, AMBER_BD = "#1A1A1A", "#5C5C5C"
BLUE_BG, BLUE_BD = "#141414", "#3A3A3A"

# (fundo, texto) dos selos de risco — branco = mais grave, como na referência
SEV_BADGE = {"CRITICAL": ("#F2F2F2", "#0A0A0A"), "HIGH": ("#BDBDBD", "#0A0A0A"),
             "MEDIUM": ("#262626", "#E6E6E6"), "LOW": ("#161616", "#8A8A8A")}

# ==============================================================================
#                    BASE DE DADOS DE DETECÇÃO
# ==============================================================================

# Clientes de xit — nomes ÚNICOS (baixa chance de falso positivo, match por substring)
CHEAT_CLIENTS = {
    # --- Clientes Premium / Pagos / Ghost ---
    "vapeprime": ("Vape Prime (Ghost)", "CRITICAL"), "vape v3": ("Vape V3", "CRITICAL"),
    "vape v4": ("Vape V4", "CRITICAL"), "vape lite": ("Vape Lite", "CRITICAL"),
    "vape-launcher": ("Vape Launcher", "CRITICAL"), "vape client": ("Vape Client", "CRITICAL"),
    "vape-client": ("Vape Client", "CRITICAL"), "vapev4": ("Vape V4", "CRITICAL"),
    "novoline": ("Novoline", "CRITICAL"), "sigma client": ("Sigma Client", "CRITICAL"),
    "sigmaclient": ("Sigma Client", "CRITICAL"), "sigma jello": ("Sigma Jello", "CRITICAL"),
    "sigma 5": ("Sigma 5.0", "CRITICAL"), "futureclient": ("Future Client", "CRITICAL"),
    "future-client": ("Future Client", "CRITICAL"), "future client": ("Future Client", "CRITICAL"),
    "riseclient": ("Rise Client", "CRITICAL"), "rise-client": ("Rise Client", "CRITICAL"),
    "rise client": ("Rise Client", "CRITICAL"), "jigsawclient": ("Jigsaw Client", "CRITICAL"),
    "jigsaw client": ("Jigsaw Client", "CRITICAL"), "moonclient": ("Moon Client", "CRITICAL"),
    "moon client": ("Moon Client", "CRITICAL"), "slinky hack": ("Slinky Hack", "CRITICAL"),
    "slinkyhack": ("Slinky Hack", "CRITICAL"), "fluxclient": ("Flux Client", "CRITICAL"),
    "flux client": ("Flux Client", "CRITICAL"), "flux b": ("Flux B", "CRITICAL"),
    "inertia client": ("Inertia Client", "CRITICAL"), "rusherhack": ("Rusher Hack", "CRITICAL"),
    "rusher hack": ("Rusher Hack", "CRITICAL"), "cetusclient": ("Cetus Client", "CRITICAL"),
    "cetus client": ("Cetus Client", "CRITICAL"), "photon client": ("Photon Client", "CRITICAL"),
    "astolfo": ("Astolfo Client", "CRITICAL"), "ares client": ("Ares Client", "CRITICAL"),
    "reset++": ("Reset++ (Ghost)", "CRITICAL"), "resetpp": ("Reset++ (Ghost)", "CRITICAL"),
    "winterware": ("Winterware", "CRITICAL"), "wintware": ("Winterware", "CRITICAL"),
    "sushi client": ("Sushi Client", "CRITICAL"), "cosmos client": ("Cosmos Client", "CRITICAL"),
    "autumn client": ("Autumn Client", "CRITICAL"), "doomsday": ("Doomsday Client", "CRITICAL"),
    "cracked client": ("Cracked Client", "HIGH"), "matrix client": ("Matrix Client", "CRITICAL"),
    "zeroday client": ("ZeroDay Client", "CRITICAL"), "zeroday-client": ("ZeroDay Client", "CRITICAL"),
    "kamiblue": ("KAMI Blue", "CRITICAL"), "kami blue": ("KAMI Blue", "CRITICAL"),
    "ambient client": ("Ambient (Vape antigo)", "CRITICAL"), "awake client": ("Awake Client", "CRITICAL"),
    "ripple client": ("Ripple Client", "CRITICAL"), "ash client": ("Ash Client", "CRITICAL"),
    "fusion client": ("Fusion Client", "HIGH"), "cheatbreaker": ("CheatBreaker (banido)", "CRITICAL"),
    "salhack": ("Salhack", "CRITICAL"), "skillclient": ("Skill Client", "CRITICAL"),
    "konas client": ("Konas Client", "CRITICAL"), "nightmare client": ("Nightmare Client", "CRITICAL"),
    "howdoubletap": ("HowDoubleTap", "CRITICAL"), "neverhook": ("Neverhook Client", "CRITICAL"),
    "verre ghost": ("Verre Ghost", "CRITICAL"), "aiden ghost": ("Aiden Ghost", "CRITICAL"),
    "chaos ghost": ("Chaos Ghost", "CRITICAL"), "ram ghost": ("Ram Ghost", "CRITICAL"),
    "blue ghost": ("Blue Ghost", "CRITICAL"), "raven b++": ("Raven B++", "CRITICAL"),
    "ravenclient": ("Raven Client", "CRITICAL"), "raven-client": ("Raven Client", "CRITICAL"),
    "raven client": ("Raven Client", "CRITICAL"), "impact client": ("Impact Client", "CRITICAL"),
    "impact-client": ("Impact Client", "CRITICAL"),
    # --- Novos / modernos ---
    "prestige client": ("Prestige Client", "CRITICAL"), "entropy client": ("Entropy Client", "CRITICAL"),
    "exhibition": ("Exhibition (Ghost)", "CRITICAL"), "krypton client": ("Krypton Client", "CRITICAL"),
    "augustus client": ("Augustus Client", "CRITICAL"), "expensive client": ("Expensive Client", "CRITICAL"),
    "swift client": ("Swift Client", "CRITICAL"), "taco client": ("Taco Client", "CRITICAL"),
    "zamorak client": ("Zamorak Client", "CRITICAL"), "keystone client": ("Keystone Client", "CRITICAL"),
    "loki client": ("Loki Client", "CRITICAL"), "izanami": ("Izanami (Ghost)", "CRITICAL"),
    "sapphire client": ("Sapphire Client", "CRITICAL"), "wexside": ("WexSide Client", "CRITICAL"),
    "wex client": ("Wex Client", "CRITICAL"), "neko client": ("Neko Client", "CRITICAL"),
    "nekoclient": ("Neko Client", "CRITICAL"), "moonlight client": ("Moonlight Client", "CRITICAL"),
    "polar client": ("Polar Client", "CRITICAL"), "requiem client": ("Requiem Client", "CRITICAL"),
    "omega client": ("Omega Client", "CRITICAL"), "pandora client": ("Pandora Client", "CRITICAL"),
    "lambda client": ("Lambda Client", "CRITICAL"), "trollhack": ("TrollHack", "CRITICAL"),
    "wolfram client": ("Wolfram Client", "CRITICAL"), "venom client": ("Venom Client", "CRITICAL"),
    "delerious": ("Delerious Client", "CRITICAL"), "snow client": ("Snow Client", "CRITICAL"),
    "plutonium client": ("Plutonium Client", "CRITICAL"), "asuna client": ("Asuna Client", "CRITICAL"),
    "miku client": ("Miku Client", "CRITICAL"), "sylvan client": ("Sylvan Client", "CRITICAL"),
    "avyn client": ("Avyn Client", "CRITICAL"), "nextgen client": ("NextGen Client", "CRITICAL"),
    "onetap client": ("OneTap Client", "CRITICAL"), "vega client": ("Vega Client", "CRITICAL"),
    "kqmii": ("Kqmii Client", "CRITICAL"), "saturn ghost": ("Saturn Ghost", "CRITICAL"),
    "comet client": ("Comet Client", "CRITICAL"), "eclipse client": ("Eclipse Client", "CRITICAL"),
    "nitro client": ("Nitro Client", "CRITICAL"), "scizor client": ("Scizor Client", "CRITICAL"),
    "shiza client": ("Shiza Client", "CRITICAL"), "tenacity ghost": ("Tenacity Ghost", "CRITICAL"),
    "deadcode": ("Deadcode Client", "CRITICAL"), "fdp client": ("FDP Client", "CRITICAL"),
    # --- Open Source ---
    "meteor-client": ("Meteor Client", "CRITICAL"), "meteorclient": ("Meteor Client", "CRITICAL"),
    "meteor client": ("Meteor Client", "CRITICAL"), "liquidbounce": ("LiquidBounce", "CRITICAL"),
    "liquid-bounce": ("LiquidBounce", "CRITICAL"), "wurstclient": ("Wurst Client", "CRITICAL"),
    "wurst-client": ("Wurst Client", "CRITICAL"), "wurst client": ("Wurst Client", "CRITICAL"),
    "bleachhack": ("Bleach Hack", "CRITICAL"), "aristois": ("Aristois", "CRITICAL"),
    "huzuni": ("Huzuni", "CRITICAL"), "3arthhack": ("3arthh4ck", "CRITICAL"),
    "3arthh4ck": ("3arthh4ck", "CRITICAL"), "phobos client": ("Phobos Client", "CRITICAL"),
    "flanhack": ("Flan Hack", "HIGH"), "seppuku": ("Seppuku Client", "CRITICAL"),
    "lambda-client": ("Lambda Client", "CRITICAL"),
    # --- Auxiliares ---
    "xrayultimate": ("X-Ray Ultimate", "HIGH"), "cavefinder": ("Cave Finder", "HIGH"),
    "seedcracker": ("Seed Cracker", "MEDIUM"),
    # --- Assinaturas extraídas dos JARs analisados (amostras do staff) ---
    "echoloader": ("Echo Client (loader)", "CRITICAL"), "echo client": ("Echo Client", "CRITICAL"),
    "echonative": ("Echo Client (native)", "CRITICAL"), "monoecho": ("Echo (MonoEcho)", "CRITICAL"),
    "echoware": ("Echoware", "CRITICAL"), "mirage client": ("Mirage Client", "CRITICAL"),
    "mirageloader": ("Mirage (loader)", "CRITICAL"), "jadyen": ("Echo/Mirage (jadyen)", "CRITICAL"),
    "ceejay": ("Echo Client (ceejay)", "HIGH"),
    # --- Ampliação v6.1 (ghost / injetáveis / modernos) ---
    "argon client": ("Argon Client", "CRITICAL"), "argonclient": ("Argon Client", "CRITICAL"),
    "thunderhack": ("ThunderHack", "CRITICAL"), "thunder hack": ("ThunderHack", "CRITICAL"),
    "nursultan": ("Nursultan Client", "CRITICAL"), "celestial client": ("Celestial Client (xit)", "CRITICAL"),
    "wild client": ("Wild Client", "CRITICAL"), "wildclient": ("Wild Client", "CRITICAL"),
    "catlean": ("Catlean Client", "CRITICAL"), "francium": ("Francium Client", "CRITICAL"),
    "grim bypass": ("Grim Bypass", "CRITICAL"), "grimbypass": ("Grim Bypass", "CRITICAL"),
    "skilled client": ("Skilled Client", "CRITICAL"), "breeze client": ("Breeze Client", "CRITICAL"),
    "dope client": ("Dope Client", "CRITICAL"), "dopeclient": ("Dope Client", "CRITICAL"),
    "drip client": ("Drip Lite", "CRITICAL"), "driplite": ("Drip Lite", "CRITICAL"),
    "drip lite": ("Drip Lite", "CRITICAL"), "manthe ghost": ("Manthe Ghost", "CRITICAL"),
    "elixir client": ("Elixir Client", "CRITICAL"), "itami ghost": ("Itami Ghost", "CRITICAL"),
    "koid client": ("Koid Client", "CRITICAL"), "gamesense client": ("GameSense Client", "CRITICAL"),
    "kami client": ("KAMI Client", "CRITICAL"), "forgehax": ("ForgeHax", "CRITICAL"),
    "inertiaclient": ("Inertia Client", "CRITICAL"), "wurst7": ("Wurst 7", "CRITICAL"),
    "coffee client": ("Coffee Client", "CRITICAL"), "coffeeclient": ("Coffee Client", "CRITICAL"),
    "boze client": ("Boze Client", "CRITICAL"), "bozeclient": ("Boze Client", "CRITICAL"),
    "atomic client": ("Atomic Client", "CRITICAL"), "vulcan client": ("Vulcan Client", "CRITICAL"),
    "skid client": ("Skid Client", "HIGH"), "lucid client": ("Lucid Client", "CRITICAL"),
    "vestige client": ("Vestige Client", "CRITICAL"), "tenacity client": ("Tenacity Client", "CRITICAL"),
    "dortware": ("Dortware", "CRITICAL"), "hanabi client": ("Hanabi Client", "CRITICAL"),
    "remix client": ("Remix Client", "CRITICAL"), "zeroday b": ("ZeroDay B", "CRITICAL"),
    "exhibition client": ("Exhibition (Ghost)", "CRITICAL"), "acrimony": ("Acrimony Client", "CRITICAL"),
    "drek client": ("Drek Client", "CRITICAL"), "whiteout ghost": ("Whiteout Ghost", "CRITICAL"),
    "rektsky": ("RektSky Client", "CRITICAL"), "nightx": ("NightX Client", "CRITICAL"),
    "lunarhack": ("Lunar Hack", "CRITICAL"), "lunar hack": ("Lunar Hack", "CRITICAL"),
    "lunar crack": ("Lunar Crack (injetado)", "CRITICAL"), "feather hack": ("Feather Hack", "CRITICAL"),
    "badlion hack": ("Badlion Hack", "CRITICAL"), "ghost client": ("Ghost Client", "HIGH"),
    "ghostclient": ("Ghost Client", "HIGH"), "injectable client": ("Cliente injetável", "CRITICAL"),
}

# Palavras COMUNS — só detectam com boundary + extensão executável/jar
STRICT_CHEAT_WORDS = {
    "future": ("Future Client", "CRITICAL"), "raven": ("Raven Client", "CRITICAL"),
    "vape": ("Vape Client", "CRITICAL"), "sigma": ("Sigma Client", "CRITICAL"),
    "impact": ("Impact Client", "CRITICAL"), "matrix": ("Matrix Client", "CRITICAL"),
    "flux": ("Flux Client", "CRITICAL"), "rise": ("Rise Client", "CRITICAL"),
    "moon": ("Moon Client", "CRITICAL"), "cetus": ("Cetus Client", "CRITICAL"),
    "cosmos": ("Cosmos Client", "CRITICAL"), "sushi": ("Sushi Client", "CRITICAL"),
    "phobos": ("Phobos Client", "CRITICAL"), "ares": ("Ares Client", "CRITICAL"),
    "photon": ("Photon Client", "CRITICAL"), "wurst": ("Wurst Client", "CRITICAL"),
    "meteor": ("Meteor Client", "CRITICAL"), "jigsaw": ("Jigsaw Client", "CRITICAL"),
    "nodus": ("Nodus", "CRITICAL"), "reach": ("Reach Client", "HIGH"),
    "fusion": ("Fusion Client", "HIGH"), "cracked": ("Cracked Client", "HIGH"),
    "baritone": ("Baritone", "MEDIUM"), "xray": ("X-Ray Mod", "HIGH"),
    "freecam": ("Freecam Mod", "HIGH"), "fullbright": ("Fullbright Mod", "MEDIUM"),
    "entropy": ("Entropy Client", "CRITICAL"), "prestige": ("Prestige Client", "CRITICAL"),
    "krypton": ("Krypton Client", "CRITICAL"), "wolfram": ("Wolfram Client", "CRITICAL"),
    "venom": ("Venom Client", "CRITICAL"), "requiem": ("Requiem Client", "CRITICAL"),
    "keystone": ("Keystone Client", "CRITICAL"),
    "argon": ("Argon Client", "CRITICAL"), "thunderhack": ("ThunderHack", "CRITICAL"),
    "nursultan": ("Nursultan Client", "CRITICAL"), "francium": ("Francium Client", "CRITICAL"),
    "boze": ("Boze Client", "CRITICAL"), "drip": ("Drip Lite", "CRITICAL"),
    "dope": ("Dope Client", "HIGH"), "elixir": ("Elixir Client", "HIGH"),
    "vulcan": ("Vulcan Client", "HIGH"), "lucid": ("Lucid Client", "HIGH"),
    "itami": ("Itami Ghost", "CRITICAL"), "manthe": ("Manthe Ghost", "CRITICAL"),
}

EXECUTABLE_EXTS = (".jar", ".exe", ".dll", ".bat", ".cmd", ".ps1", ".vbs", ".msi", ".jnlp", ".scr")

# Prefixos de pacote de MODS/LIBS LEGÍTIMOS — se o .jar é feito majoritariamente
# destes pacotes, não marcamos por "ofuscação" ou palavras fracas (anti-falso-positivo).
LEGIT_PACKAGE_PREFIXES = (
    "net/minecraft", "com/mojang", "net/fabricmc", "net/minecraftforge",
    "net/neoforged", "org/quiltmc", "net/optifine", "optifine/",
    "me/jellysquid", "net/caffeinemc", "org/spongepowered", "me/shedaniel",
    "com/terraformersmc", "dev/architectury", "software/bernie/geckolib",
    "mezz/jei", "journeymap/", "xaero/", "net/blay09",
    "com/llamalad7", "org/apache", "com/google", "org/slf4j", "kotlin/",
    "org/jetbrains", "com/electronwill", "org/joml", "org/lwjgl",
    "appeng/", "mekanism/", "vazkii/", "slimeknights/",
    "org/objectweb", "it/unimi", "com/mysql", "org/json",
)

# Módulos de xit FORTES — nome específico o bastante p/ não dar falso positivo.
# Match por substring no bytecode/caminho das classes.
JAR_STRONG_KEYWORDS = [
    "killaura", "kill_aura", "aimbot", "aimassist", "aim_assist", "smoothaim",
    "silentaim", "silent_aim", "aurabot", "clickaura", "triggerbot",
    "autoscaffold", "scaffoldwalk", "autotower",
    "fastbreak", "fastplace", "fasteat", "fastbow", "speedmine", "autonuke",
    "flyhack", "creativefly", "elytrafly", "packetfly",
    "packetkick", "fakelag", "antikb", "antiknockback",
    "autocritical", "chestesp", "entityesp", "playeresp", "mobesp",
    "xrayclient", "orebright", "orefinder",
    "autoclicker", "autoclick", "leftclicker", "rightclicker", "autoblock",
    "autototem", "autocrystal", "crystalaura", "crystal_aura",
    "autoanchor", "autocity", "selfdestruct", "cheststealer", "chatspam",
    "autopotion", "antibot", "speedhack", "omnisprint", "legitspeed",
    "noslowdown", "bunnyhop",
    "wallhack", "wall_hack", "forcefield",
    "lagswitch", "hackmodule", "cheatmodule", "cheatengine",
    "vapev4", "vapev3", "vape-loader", "vapeloader", "sigmaapi", "sigma/loader",
    "meteordevelopment", "liquidbounce", "wurstclient", "impact/client",
    "cheatbreaker", "entropy/module", "ghostclient",
    # --- Marcas internas vistas nos JARs analisados ---
    "hack/echo/client", "echohudelement", "dev/jadyen", "dev.jadyen",
    "mirage/loader", "miragestreamhandler", "echonative",
    # --- Ampliação v6.1 ---
    "anchoraura", "autoanchor", "bedaura", "autobed", "holefiller", "autotrap",
    "autoweb", "webaura", "autocrit", "reachhack", "reach_hack",
    "aimbotmodule", "clickgui", "autoclickermodule",
    "jitterclick", "doubleclicker", "butterflyclick", "cpsbypass",
    "velocitybypass", "antivelocity", "noslowbypass", "timerhack",
    "packetcancel", "anticheatdisabler", "grimdisabler", "watchdogbypass",
    "thunderhack", "nursultan", "argonclient", "wurst/hack", "meteordevelopment/meteorclient",
    "net/ccbluex", "ccbluex", "xyz/greaj", "me/zero/clarinet", "selfdestructmodule",
]

# Palavras FRACAS — aparecem em código legítimo. Só contam quando:
#  (a) vierem com word-boundary no bytecode, E
#  (b) houver >= 2 fracas distintas OU 1 forte junto, E
#  (c) o jar NÃO for majoritariamente de pacote legítimo.
JAR_WEAK_KEYWORDS = [
    "scaffold", "nofall", "noslow", "velocity", "criticals", "nuker",
    "freecam", "freelook", "fullbright", "autoarmor", "autopot", "autoheal",
    "autototem", "reachmod", "hitbox", "bhop", "spider", "jesus", "blink",
    "phaseclip", "fastplace", "tracers", "surround",
]

# Mantido para compatibilidade: superconjunto usado em varredura rápida de nomes.
JAR_KEYWORDS = JAR_STRONG_KEYWORDS + JAR_WEAK_KEYWORDS

# Nomes de bibliotecas nativas que NÃO deveriam existir dentro de um mod de Minecraft
NATIVE_LIB_MARKERS = (".dll", ".dylib", ".so", ".jnilib")

# Software legítimo conhecido — NÃO marcar como xit (reduz falso positivo).
# Checado por igualdade de "token" normalizado do nome do arquivo/processo.
LEGIT_SOFTWARE = {
    "optifine", "sodium", "lithium", "phosphor", "iris", "fabric api", "fabric-api",
    "fabricloader", "fabric loader", "fabric", "forge", "neoforge", "quilt", "cloth config",
    "modmenu", "mod menu", "architectury", "yacl", "geckolib", "jei", "rei", "emi",
    "journeymap", "xaeros minimap", "xaero", "voxelmap", "appleskin", "ferritecore",
    "lazydfu", "starlight", "entityculling", "dynamicfps", "betterfps", "controlling",
    "lunar", "lunarclient", "lunar client", "badlion", "badlionclient", "badlion client",
    "feather", "feather client", "labymod", "essential", "pollymc", "prismlauncher",
    "obs", "obs studio", "obs64", "streamlabs", "discord", "discordptb", "discordcanary",
    "spotify", "steam", "epicgameslauncher", "nvidia", "geforce", "radeon", "msi afterburner",
    "java", "javaw", "javaws", "python", "chrome", "firefox", "msedge", "brave",
    "explorer", "notepad", "code", "windowsterminal", "powershell", "cmd",
}

# Palavras genéricas que SOZINHAS geram muito falso positivo.
# Só contam se vierem com outro sinal (dentro de .jar/.exe, bytecode de xit, ou Java do jogo).
GENERIC_WEAK_WORDS = {
    "hack", "cheat", "client", "mod", "ghost", "boost", "fps", "optimizer", "macro", "fast",
}

# Autoclickers e ferramentas de macro
AUTOCLICKERS = {
    "opautoclicker": "OP Autoclicker", "op autoclicker": "OP Autoclicker", "op_autoclicker": "OP Autoclicker",
    "gsautoclicker": "GS Auto Clicker", "gs autoclicker": "GS Auto Clicker",
    "fastautoclicker": "Fast Autoclicker", "freeautoclicker": "Free Autoclicker",
    "speedautoclicker": "Speed Autoclicker", "roblox autoclick": "Roblox Autoclicker",
    "murgee": "Murgee AutoClicker", "clickerheroes": "ClickerHeroes Auto",
    "perfectclick": "Perfect Clicker", "autoclicker": "Autoclicker Genérico",
    "auto-clicker": "Autoclicker Genérico", "auto_clicker": "Autoclicker Genérico",
    "clickermann": "ClickerMann", "opac": "OP AC", "mousemacro": "Mouse Macro",
    "mini mouse macro": "Mini Mouse Macro", "minimousemacro": "Mini Mouse Macro",
    "perfect keyboard": "Perfect Keyboard", "perfectkeyboard": "Perfect Keyboard",
    "autohotkey": "AutoHotkey (verificar scripts)", "ahk": "AutoHotkey Script",
    "razer synapse": "Razer Synapse (macros)", "razersynapse": "Razer Synapse (macros)",
    "logitech ghub": "Logitech GHub (macros)", "logitechghub": "Logitech GHub (macros)",
    "logitech gaming": "Logitech LGS (macros)", "bloody": "Bloody Software (X7)",
    "bloody7": "Bloody 7", "a4 tech": "A4Tech (Bloody firmware)", "rewasd": "reWASD (remap)",
    "xmouse": "X-Mouse Button Control", "keyremapper": "Key Remapper", "clickfinity": "Clickfinity",
    "clickbot": "Click Bot", "corsair icue": "Corsair iCUE (macros)", "corsairicue": "Corsair iCUE (macros)",
    "rog armory": "ROG Armory (macros)", "rogarmory": "ROG Armory (macros)",
    # novos
    "tinytask": "TinyTask (macro)", "mouse recorder": "Mouse Recorder", "mouserecorder": "Mouse Recorder",
    "jitterclicker": "Jitter Clicker", "jitter clicker": "Jitter Clicker",
    "butterfly clicker": "Butterfly Clicker", "butterflyclicker": "Butterfly Clicker",
    "dragclick": "Drag Clicker", "drag clicker": "Drag Clicker", "dragclicker": "Drag Clicker",
    "pro autoclicker": "Pro Autoclicker", "nextclicker": "Next Clicker",
    "fire clicker": "Fire Clicker", "fireclicker": "Fire Clicker", "speed clicker": "Speed Clicker",
    "kyle autoclicker": "Kyle's Autoclicker", "orphamiel": "Orphamiel Autoclicker",
    "autofire": "AutoFire", "auto keyboard": "Auto Keyboard Presser", "autoclickextreme": "AutoClick Extreme",
    "clickmania": "ClickMania", "easyclicker": "Easy Clicker", "mouse clicker": "Mouse Clicker",
    # ampliação v6.1
    "maxclicker": "Max Clicker", "max clicker": "Max Clicker", "autoclicker.io": "AutoClicker.io",
    "zautoclicker": "Z Autoclicker", "polar autoclicker": "Polar Autoclicker",
    "kronos clicker": "Kronos Clicker", "kronosclicker": "Kronos Clicker",
    "jnative": "JNative Clicker", "macro recorder": "Macro Recorder", "macrorecorder": "Macro Recorder",
    "pulover": "Pulover's Macro Creator", "jitbit": "Jitbit Macro Recorder",
    "macro toolworks": "Macro Toolworks", "keyran": "Keyran (macro)", "redragon": "Redragon (macros)",
    "glorious core": "Glorious Core (macros)", "steelseries gg": "SteelSeries GG (macros)",
    "hyperx ngenuity": "HyperX NGenuity (macros)", "roccat swarm": "Roccat Swarm (macros)",
    "clicker.exe": "Clicker genérico", "cpsbooster": "CPS Booster", "cps booster": "CPS Booster",
}

# Ferramentas usadas para burlar screenshare / injeção / anti-forense
BYPASS_TOOLS = {
    "bleachbit": ("BleachBit (limpa vestígios)", "HIGH"), "ccleaner": ("CCleaner (limpa vestígios)", "LOW"),
    "privazer": ("PrivaZer", "HIGH"), "wisecleaner": ("Wise Cleaner", "LOW"),
    "usnjournal": ("USN Journal Cleaner", "CRITICAL"), "usn journal": ("USN Journal Cleaner", "CRITICAL"),
    "usnwipe": ("USN Wiper", "CRITICAL"), "journal wipe": ("Journal Wiper", "CRITICAL"),
    "prefetch cleaner": ("Prefetch Cleaner", "CRITICAL"), "prefetchcleaner": ("Prefetch Cleaner", "CRITICAL"),
    "eraser.exe": ("Eraser (secure delete)", "HIGH"), "diskwipe": ("Disk Wipe", "HIGH"),
    "sdelete": ("SDelete", "HIGH"), "shellbagcleaner": ("ShellBag Cleaner", "CRITICAL"),
    "regscrubber": ("Reg Scrubber", "HIGH"), "timestomp": ("Timestomp", "CRITICAL"),
    "setmace": ("SetMACE (timestomp)", "CRITICAL"), "shadowexplorer": ("Shadow Explorer", "MEDIUM"),
    "everything.exe": ("Everything (ocultador)", "LOW"), "processhacker": ("Process Hacker", "MEDIUM"),
    "process hacker": ("Process Hacker", "MEDIUM"), "systeminformer": ("System Informer", "MEDIUM"),
    "cheat engine": ("Cheat Engine", "CRITICAL"), "cheatengine": ("Cheat Engine", "CRITICAL"),
    "hxd": ("HxD Hex Editor", "MEDIUM"), "extreme injector": ("Extreme Injector", "CRITICAL"),
    "extremeinjector": ("Extreme Injector", "CRITICAL"), "xenos injector": ("Xenos Injector", "CRITICAL"),
    "xenosinjector": ("Xenos Injector", "CRITICAL"), "guided hacking": ("Guided Hacking Injector", "CRITICAL"),
    "gh injector": ("GH Injector", "CRITICAL"), "process explorer": ("Process Explorer", "LOW"),
    "obs virtual": ("OBS Virtual Cam (fake sshare)", "HIGH"), "e2sharer": ("E2Sharer bypass", "HIGH"),
    "screensharefaker": ("Screenshare Faker", "CRITICAL"), "fake discord": ("Fake Discord", "CRITICAL"),
    "fakediscord": ("Fake Discord", "CRITICAL"), "richpresencefaker": ("Rich Presence Faker", "HIGH"),
    "spooferpro": ("Spoofer Pro (HWID)", "CRITICAL"), "hwid spoofer": ("HWID Spoofer", "CRITICAL"),
    "hwidspoofer": ("HWID Spoofer", "CRITICAL"), "hwid-spoofer": ("HWID Spoofer", "CRITICAL"),
    "spoofer": ("HWID Spoofer", "CRITICAL"), "amidspoofer": ("AMID Spoofer", "CRITICAL"),
    "diskserial": ("Disk Serial Changer", "CRITICAL"), "macchanger": ("MAC Address Changer", "HIGH"),
    "tmac": ("TMAC (MAC changer)", "HIGH"), "lastactivityview": ("LastActivityView (auditor)", "LOW"),
    "winprefetchview": ("WinPrefetchView (auditor)", "LOW"), "shellbagsview": ("ShellBagsView (auditor)", "LOW"),
    "usrclass": ("USRCLASS manipulator", "HIGH"),
    # novos — injeção / reverse eng / disfarce / VM / remoto
    "frida": ("Frida (injeção dinâmica)", "CRITICAL"), "x64dbg": ("x64dbg (debugger)", "MEDIUM"),
    "ollydbg": ("OllyDbg (debugger)", "MEDIUM"), "scylla": ("Scylla (dumper)", "HIGH"),
    "megadumper": ("MegaDumper", "HIGH"), "de4dot": ("de4dot (deobfuscator)", "MEDIUM"),
    "dnspy": ("dnSpy (edita .NET)", "MEDIUM"), "recaf": ("Recaf (edita .jar)", "HIGH"),
    "bytecode viewer": ("Bytecode Viewer", "HIGH"), "bytecodeviewer": ("Bytecode Viewer", "HIGH"),
    "jd-gui": ("JD-GUI (descompila jar)", "MEDIUM"), "confuserex": ("ConfuserEx (ofusca)", "HIGH"),
    "themida": ("Themida (packer)", "HIGH"), "vmprotect": ("VMProtect (packer)", "HIGH"),
    "sandboxie": ("Sandboxie (rodar xit isolado)", "HIGH"), "shadow defender": ("Shadow Defender", "HIGH"),
    "deep freeze": ("Deep Freeze", "HIGH"), "vmware": ("VMware (rodar MC em VM)", "MEDIUM"),
    "virtualbox": ("VirtualBox (rodar MC em VM)", "MEDIUM"), "anydesk": ("AnyDesk (controle remoto)", "MEDIUM"),
    "teamviewer": ("TeamViewer (controle remoto)", "MEDIUM"), "parsec": ("Parsec (controle remoto)", "MEDIUM"),
    "rustdesk": ("RustDesk (controle remoto)", "MEDIUM"), "fakenitro": ("Fake Nitro", "HIGH"),
    "fake fps": ("Fake FPS Overlay", "HIGH"), "bettersafe": ("BetterSafe bypass", "CRITICAL"),
    # ampliação v6.1
    "process lasso": ("Process Lasso", "LOW"), "kdmapper": ("KDMapper (driver mapper)", "CRITICAL"),
    "kdu.exe": ("KDU (driver loader)", "CRITICAL"), "manualmap": ("Manual Map Injector", "CRITICAL"),
    "manual map": ("Manual Map Injector", "CRITICAL"), "dll injector": ("DLL Injector", "CRITICAL"),
    "dllinjector": ("DLL Injector", "CRITICAL"), "remote dll": ("Remote DLL Injector", "CRITICAL"),
    "winject": ("Winject", "CRITICAL"), "injectorx": ("InjectorX", "CRITICAL"),
    "jvm injector": ("JVM Injector", "CRITICAL"), "jvminjector": ("JVM Injector", "CRITICAL"),
    "javainjector": ("Java Injector", "CRITICAL"), "java injector": ("Java Injector", "CRITICAL"),
    "agentinjector": ("Java Agent Injector", "CRITICAL"), "jarinjector": ("JAR Injector", "CRITICAL"),
    "ssbypass": ("Screenshare Bypass", "CRITICAL"), "ss bypass": ("Screenshare Bypass", "CRITICAL"),
    "screenshare bypass": ("Screenshare Bypass", "CRITICAL"), "anti ss": ("Anti-SS", "CRITICAL"),
    "antiss": ("Anti-SS", "CRITICAL"), "selfdestruct": ("Self-Destruct (apaga xit)", "CRITICAL"),
    "self destruct": ("Self-Destruct (apaga xit)", "CRITICAL"), "stringcleaner": ("String Cleaner", "CRITICAL"),
    "string cleaner": ("String Cleaner", "CRITICAL"), "memory cleaner": ("Memory String Cleaner", "HIGH"),
    "journaltrace": ("JournalTrace (auditor)", "LOW"), "echo journal": ("Echo Journal Wipe", "CRITICAL"),
    "eventlog clear": ("Event Log Cleaner", "CRITICAL"), "eventlogcleaner": ("Event Log Cleaner", "CRITICAL"),
    "wevtutil cl": ("Limpeza de Event Log", "CRITICAL"), "bamcleaner": ("BAM Cleaner", "CRITICAL"),
    "bam cleaner": ("BAM Cleaner", "CRITICAL"), "amcache cleaner": ("Amcache Cleaner", "CRITICAL"),
    "runmru cleaner": ("RunMRU Cleaner", "CRITICAL"), "hollows hunter": ("Hollows Hunter", "LOW"),
    "ida64": ("IDA Pro (disassembler)", "MEDIUM"), "ghidra": ("Ghidra (disassembler)", "MEDIUM"),
    "reclass.net": ("ReClass (memória)", "HIGH"), "httpdebugger": ("HTTP Debugger", "MEDIUM"),
    "vpn spoof": ("VPN Spoofer", "HIGH"), "volumeid": ("VolumeID (serial changer)", "CRITICAL"),
}

SUSPICIOUS_PROCESSES = list(CHEAT_CLIENTS.keys()) + list(AUTOCLICKERS.keys()) + list(BYPASS_TOOLS.keys())

# Ferramentas que o PRÓPRIO staff usa na SS (System Informer, Everything, AnyDesk...).
# Aparecem só como informação em "Sistema" — nunca contam como xit.
INFO_TOOL_KEYS = {
    "everything.exe", "processhacker", "process hacker", "systeminformer", "hxd", "process explorer",
    "lastactivityview", "winprefetchview", "shellbagsview", "journaltrace", "hollows hunter",
    "x64dbg", "ollydbg", "dnspy", "de4dot", "jd-gui", "ida64", "ghidra", "httpdebugger",
    "vmware", "virtualbox", "anydesk", "teamviewer", "parsec", "rustdesk", "process lasso",
    "shadowexplorer",
}

# Software de mouse/teclado: legítimo, mas permite macro -> só MÉDIO ("verificar macros").
MOUSE_SOFTWARE_KEYS = {
    "razer synapse", "razersynapse", "logitech ghub", "logitechghub", "logitech gaming", "bloody",
    "bloody7", "a4 tech", "corsair icue", "corsairicue", "rog armory", "rogarmory", "redragon",
    "glorious core", "steelseries gg", "hyperx ngenuity", "roccat swarm", "xmouse", "rewasd",
    "keyremapper", "autohotkey",
}

# Só nomes ESPECÍFICOS de xit — palavras genéricas ("vape", "jigsaw", "entropy",
# "injector", "scaffold") foram removidas porque aparecem em logs normais do jogo/Mixin.
TEXT_SUSPICIOUS_STRINGS = [
    "vapeprime", "vape v4", "vape lite", "meteor client", "meteor-client", "liquidbounce", "wurstclient",
    "wurst client", "impact client", "sigma client", "future client", "rise client", "rusherhack",
    "novoline", "salhack", "aristois", "kamiblue", "kami blue", "bleachhack", "thunderhack",
    "nursultan", "argon client", "boze client", "drip lite", "raven b++", "doomsday client",
    "killaura", "kill_aura", "aimbot", "silentaim", "aimassist", "triggerbot", "autoscaffold",
    "flyhack", "autoclicker", "auto-clicker", "leftclicker", "chestesp", "entityesp", "xrayclient",
    "autototem", "autocrystal", "crystalaura", "crystal aura", "anchoraura", "clickgui",
    "extremeinjector", "xenosinjector", "gh injector", "dllinject", "hwid spoof", "spooferpro",
    "usn journal wipe", "prefetch cleaner", "shellbag clean", "timestomp", "kdmapper", "manualmap",
    "ss bypass", "grim disabler", "watchdog bypass", "velocity bypass", "jitterclick", "butterfly click",
    "vape crack", "sigma crack", "krypton crack", "-javaagent:vape", "-javaagent:meteor",
]
# Termos que indicam o PRÓPRIO xit carregando (não uma conversa no chat)
TEXT_STRONG_HITS = ("killaura", "aimbot", "silentaim", "aimassist", "triggerbot", "autocrystal",
                    "crystalaura", "anchoraura", "clickgui", "autototem", "-javaagent:")
_LOAD_VERBS = r"(?:loading|loaded|load(?:ing)? mod|initiali[sz]\w*|injected|launching|starting|inject\w*|module|enabled|toggled)"


def _loaded_kw(line, kw):
    """O verbo de carregamento vem LOGO antes do termo, ou o termo vem antes de 'enabled/toggled on'."""
    k = re.escape(kw)
    return bool(re.search(_LOAD_VERBS + r"\W{1,3}(?:mod\W{1,3})?" + k, line) or
                re.search(k + r"\W{1,3}(?:enabled|toggled on|activated|injected)", line))

TEXT_EXTS = (".txt", ".log", ".json", ".yml", ".yaml", ".cfg", ".ini", ".properties")

# Extensões em que um NOME de xit faz sentido (imagens, vídeos, docs nunca são marcados)
RELEVANT_EXTS = EXECUTABLE_EXTS + (".zip", ".rar", ".7z", ".ahk", ".pf", ".lnk", ".py", ".pyw",
                                   ".amc", ".mcr", ".rec", ".xml")
ARCHIVE_EXTS = (".zip", ".rar", ".7z")
SCRIPT_EXTS = (".bat", ".cmd", ".ps1", ".vbs", ".ahk", ".py", ".pyw")

# Palavras que, junto de uma palavra comum (vape, raven, flux...), confirmam que é xit num .exe
STRICT_CONTEXT = ("client", "ghost", "hack", "loader", "inject", "crack", "cheat", "b++",
                  "bypass", "clicker", "v3", "v4", "v5", "minecraft", "mc")
# Nomes de xit que também são palavras/personagens comuns: só valem em .exe/.jar/.dll
AMBIGUOUS_CLIENT_WORDS = {"astolfo", "exhibition", "doomsday", "seppuku", "izanami", "francium", "acrimony",
                          "delerious", "deadcode", "nightx", "ceejay", "catlean", "nursultan", "huzuni",
                          "salhack", "wexside", "kqmii", "rektsky", "dortware", "jadyen", "aristois"}
# Palavras únicas o bastante para marcar mesmo com o nome "puro" (vape.exe, raven.exe)
STRICT_EXACT_OK = {"vape", "raven", "wurst", "nodus", "cetus", "phobos", "drip", "itami", "manthe",
                   "francium", "nursultan", "thunderhack", "boze", "sigma", "jigsaw"}

# Fabricantes confiáveis — binários assinados por eles não são xit (anti-falso-positivo)
TRUSTED_VENDORS = (b"Microsoft Corporation", b"NVIDIA Corporation", b"Google LLC", b"Google Inc",
                   b"Mozilla Corporation", b"Valve Corporation", b"Discord Inc", b"Oracle Corporation",
                   b"Intel Corporation", b"Advanced Micro Devices", b"Adobe", b"Epic Games", b"Riot Games",
                   b"Spotify", b"Opera Norway", b"Brave Software", b"Mojang", b"Overwolf", b"OBS Project",
                   b"Realtek", b"Logitech", b"Razer", b"Corsair", b"SteelSeries", b"Eclipse Adoptium",
                   b"Azul Systems", b"Amazon.com", b"JetBrains", b"Python Software Foundation", b"Dropbox",
                   b"Zoom Video", b"Apple Inc", b"Electronic Arts", b"Ubisoft", b"Rockstar Games", b"Blizzard")
_VENDOR_RE = re.compile(b"C\x00o\x00m\x00p\x00a\x00n\x00y\x00N\x00a\x00m\x00e\x00\x00\x00(?:\x00\x00)?((?:[^\x00]\x00){2,80})")

# IDs de mods (fabric.mod.json / mods.toml) que SÃO xit ou vantagem ilegal
CHEAT_MOD_IDS = {
    "meteor-client": ("Meteor Client", "CRITICAL"), "wurst": ("Wurst Client", "CRITICAL"),
    "liquidbounce": ("LiquidBounce", "CRITICAL"), "aristois": ("Aristois", "CRITICAL"),
    "bleachhack": ("BleachHack", "CRITICAL"), "inertia": ("Inertia Client", "CRITICAL"),
    "thunderhack": ("ThunderHack", "CRITICAL"), "boze": ("Boze Client", "CRITICAL"),
    "rusherhack": ("RusherHack", "CRITICAL"), "impact": ("Impact Client", "CRITICAL"),
    "kamiblue": ("KAMI Blue", "CRITICAL"), "lambda": ("Lambda Client", "CRITICAL"),
    "future": ("Future Client", "CRITICAL"), "coffee": ("Coffee Client", "CRITICAL"),
    "argon": ("Argon Client", "CRITICAL"), "francium": ("Francium Client", "CRITICAL"),
    "xray": ("X-Ray Mod", "HIGH"), "advanced-xray": ("Advanced X-Ray", "HIGH"),
    "advancedxray": ("Advanced X-Ray", "HIGH"), "xrayultimate": ("X-Ray Ultimate", "HIGH"),
    "autototem": ("AutoTotem Mod", "HIGH"), "auto-totem": ("AutoTotem Mod", "HIGH"),
    "reach": ("Reach Mod", "CRITICAL"), "hitboxes": ("Hitbox Mod", "HIGH"),
    "freecam": ("Freecam Mod", "HIGH"), "baritone": ("Baritone (bot)", "MEDIUM"),
    "seedcracker": ("SeedCracker", "MEDIUM"), "autoclicker": ("AutoClicker Mod", "CRITICAL"),
    "cheatutils": ("Cheat Utils", "CRITICAL"), "fullbright": ("Fullbright Mod", "MEDIUM"),
}

# Nomes de MÓDULOS de hack client (KillAura.class, Reach.class...). Contados dentro de
# pastas module(s)/hack(s)/feature(s)/cheat(s) => estrutura típica de cliente de xit.
CHEAT_MODULE_NAMES = {
    "killaura", "aura", "reach", "velocity", "aimassist", "aimbot", "autoclicker", "triggerbot",
    "scaffold", "fly", "flight", "speed", "nofall", "esp", "tracers", "xray", "fullbright",
    "criticals", "nuker", "fastplace", "fastbreak", "timer", "blink", "freecam", "antibot",
    "hitbox", "hitboxes", "autototem", "crystalaura", "autocrystal", "anchoraura", "autoarmor",
    "autopot", "cheststealer", "noslow", "spider", "jesus", "step", "phase", "bhop", "longjump",
    "highjump", "antiknockback", "antikb", "wtap", "sprintreset", "autoblock", "backtrack",
    "fakelag", "nametags", "chams", "wallhack", "clickgui", "selfdestruct", "surround", "autotrap",
    "holefiller", "bedaura", "autoweb", "disabler", "rightclicker", "leftclicker", "jitterclick",
}
_MODULE_DIR_RE = re.compile(r"/(?:modules?|hacks?|features?|cheats?|impl/module|mods?/(?:combat|movement|render|player|world))/")
_MODULE_CATS = {"combat", "movement", "render", "player", "world", "misc", "exploit", "ghost", "blatant", "legit"}

# Texture packs ilegais (overlay, anti-invis, xray)
ILLEGAL_PACK_WORDS = ("xray", "x-ray", "x ray", "antiinvis", "anti invis", "anti-invis", "seeinvis",
                      "see invis", "ore outline", "ore overlay", "oreoverlay", "ore highlight", "ores glow",
                      "glowing ores", "invisible stone", "transparent stone", "clear stone", "invis stone",
                      "bedrock overlay", "hitbox overlay", "player esp")

# Pastas de mods dos launchers a serem vasculhadas em profundidade
def get_mod_dirs():
    dirs = []
    home = os.path.expanduser("~")
    appdata = os.environ.get("APPDATA", os.path.join(home, "AppData", "Roaming"))
    for base, sub in [
        (".minecraft", "mods"), (".minecraft", "versions"),
        (".lunarclient", ""), (".feather", ""), (".badlion", ""),
        ("PrismLauncher", "instances"), (".curseforge", ""),
        ("gg.essential", ""), (".technic", "modpacks"),
        (".tlauncher", ""), ("ModrinthApp", ""), ("PolyMC", "instances"), ("MultiMC", "instances"),
        (".sklauncher", ""), ("ATLauncher", "instances"), ("gdlauncher_next", "instances"),
        ("com.modrinth.theseus", "profiles"),
    ]:
        p = os.path.join(appdata, base, sub) if sub else os.path.join(appdata, base)
        if os.path.exists(p):
            dirs.append(p)
    return dirs


def get_priority_dirs():
    dirs = []
    home = os.path.expanduser("~")
    appdata = os.environ.get("APPDATA", os.path.join(home, "AppData", "Roaming"))
    localdata = os.environ.get("LOCALAPPDATA", os.path.join(home, "AppData", "Local"))
    for p in [
        os.path.join(appdata, ".minecraft"), os.path.join(appdata, ".technic"),
        os.path.join(appdata, ".curseforge"), os.path.join(appdata, ".lunarclient"),
        os.path.join(appdata, "PrismLauncher"), os.path.join(appdata, "gg.essential"),
        os.path.join(appdata, ".feather"), os.path.join(appdata, ".badlion"),
        os.path.join(appdata, "ModrinthApp"), os.path.join(appdata, ".tlauncher"),
        os.path.join(appdata, "PolyMC"), os.path.join(appdata, ".sklauncher"), os.path.join(appdata, "ATLauncher"),
        os.path.join(appdata, "gdlauncher_next"), os.path.join(appdata, "com.modrinth.theseus"),
        os.path.join(localdata, "Programs"), os.path.join(localdata, "Temp"),
        os.path.join(home, "Downloads"), os.path.join(home, "Desktop"),
        os.path.join(home, "Documents"), os.path.join(home, "Documents", "AutoHotkey"),
        os.path.join(home, "Videos"), r"C:\Windows\Prefetch",
    ]:
        if os.path.exists(p):
            dirs.append(p)
    return dirs


# ==============================================================================
#                    UTILITÁRIOS DE VARREDURA
# ==============================================================================

def norm(s: str) -> str:
    return re.sub(r"[\s_\-\.]+", " ", s.lower()).strip()


SEV_RANK_E = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}


def worst_sev(*sevs):
    sevs = [s for s in sevs if s]
    return min(sevs, key=lambda s: SEV_RANK_E.get(s, 3)) if sevs else None


def _has_word_boundary(text: str, word: str) -> bool:
    pattern = r"(?:^|[^a-z0-9])" + re.escape(word) + r"(?:$|[^a-z0-9])"
    return bool(re.search(pattern, text))


def is_legit_name(name: str) -> bool:
    """True se o nome bate com software legítimo conhecido (anti-falso-positivo)."""
    n = norm(name)
    base = n.rsplit(".", 1)[0] if "." in n else n
    for legit in LEGIT_SOFTWARE:
        if base == legit or n == legit:
            return True
        # nome COMEÇA com o software legítimo (ex.: "sodium-fabric-0.5.jar").
        # "raven-fabric.jar" NÃO é liberado (o legítimo não é o nome principal).
        if len(legit) >= 4 and (base == legit or base.startswith(legit + " ")):
            return True
    return False


def _trie_pattern(words):
    """Monta uma regex em árvore (prefixos em comum) — muito mais rápida que a|b|c|... gigante."""
    trie = {}
    for w in words:
        node = trie
        for ch in w:
            node = node.setdefault(ch, {})
        node[""] = True

    def build(node):
        end = "" in node
        keys = sorted(k for k in node if k)
        if not keys:
            return ""
        alts = [re.escape(k) + build(node[k]) for k in keys]
        single = [re.escape(k) for k in keys if len(node[k]) == 1 and "" in node[k]]
        if len(alts) == 1:
            res = alts[0]
        elif len(single) == len(alts):
            res = "[" + "".join(single) + "]"
        else:
            res = "(?:" + "|".join(alts) + ")"
        return "(?:" + res + ")?" if end else res

    return build(trie)


def _norm_key(k: str) -> str:
    # chaves comparadas com o nome normalizado (ex.: "vape-client" -> "vape client")
    return norm(k)


def _key_matches(key: str, n: str) -> bool:
    # chaves curtas (<=4) exigem fronteira de palavra (evita "opac" em "opacity")
    if len(key) <= 4:
        return _has_word_boundary(n, key)
    return key in n


def _build_prefilter(keys):
    keys = {k for k in keys if k}
    return re.compile(_trie_pattern(keys)) if keys else None


_CHEAT_KEYS = [(k, _norm_key(k), v) for k, v in CHEAT_CLIENTS.items()]
_AUTO_KEYS = [(k, _norm_key(k), v) for k, v in AUTOCLICKERS.items()]
_BYPASS_KEYS = [(k, _norm_key(k), v) for k, v in BYPASS_TOOLS.items()]
_ANY_KEY_RE = _build_prefilter([k for k, _, _ in _CHEAT_KEYS + _AUTO_KEYS + _BYPASS_KEYS] +
                               [nk for _, nk, _ in _CHEAT_KEYS + _AUTO_KEYS + _BYPASS_KEYS])


def _has_relevant_ext(fname_lower: str) -> bool:
    base = fname_lower.rsplit("\\", 1)[-1].rsplit("/", 1)[-1]
    if "." not in base:
        return True
    ext = "." + base.rsplit(".", 1)[-1]
    # extensões "numéricas"/versão (ex.: "vape v4.2") contam como sem extensão
    if len(ext) > 6 or ext[1:].replace("_", "").isdigit():
        return True
    return base.endswith(RELEVANT_EXTS)


def scan_filename(filename: str, require_strict: bool = True):
    hits = []
    if not filename:
        return hits
    fname_lower = filename.lower()
    if not _has_relevant_ext(fname_lower):
        return hits
    n = norm(filename)
    is_exec = fname_lower.endswith(EXECUTABLE_EXTS)
    is_jar = fname_lower.endswith(".jar")
    # pré-filtro rápido: se nenhuma chave aparece, só sobram as palavras estritas
    quick = bool(_ANY_KEY_RE and (_ANY_KEY_RE.search(n) or _ANY_KEY_RE.search(fname_lower)))
    if not quick and not is_exec:
        return hits
    seen = set()

    def push(label, kind, sev, ev):
        if (label, kind) not in seen:
            seen.add((label, kind))
            hits.append((label, kind, sev, ev))

    if quick:
        # Assinaturas fortes (nome único de xit) ignoram whitelist — nome já é prova.
        for key, nkey, (label, sev) in _CHEAT_KEYS:
            if key in AMBIGUOUS_CLIENT_WORDS and not is_exec:
                continue
            if _key_matches(nkey, n) or _key_matches(key, fname_lower):
                push(label, "CHEAT", sev, f"name~{key}")
    # Se bate whitelist e nenhuma assinatura forte apareceu, trata como legítimo.
    if not hits and is_legit_name(filename):
        return []
    # Palavra comum (vape, raven, flux, impact...) só vale em .jar, ou em .exe/.dll
    # quando vier junto de contexto de xit ("vape lite.exe", "raven b++ loader.exe").
    if is_exec and not hits:
        stem = norm(fname_lower.rsplit(".", 1)[0])
        has_ctx = (is_jar or stem in STRICT_EXACT_OK or (stem.split() or [""])[0] in STRICT_EXACT_OK or
                   "b++" in stem or any(_has_word_boundary(stem, c) for c in STRICT_CONTEXT))
        if has_ctx:
            for word, (label, sev) in STRICT_CHEAT_WORDS.items():
                if word in GENERIC_WEAK_WORDS:
                    continue
                if _has_word_boundary(n, word):
                    if is_jar and word not in STRICT_EXACT_OK:
                        # krypton, reach, fusion... também são mods legítimos: o nome sozinho é só
                        # informativo; quem confirma é a análise interna do jar.
                        push(f"Nome lembra {label}", "CHEAT", "LOW", f"strict:{word}+jar (confirmar conteúdo)")
                    else:
                        push(label, "CHEAT", sev if is_jar else ("HIGH" if sev == "CRITICAL" else sev),
                             f"strict:{word}+{'jar' if is_jar else 'contexto'}")
    if quick:
        for key, nkey, label in _AUTO_KEYS:
            if _key_matches(nkey, n) or _key_matches(key, fname_lower):
                if key in MOUSE_SOFTWARE_KEYS:
                    push(f"{label} — verificar macros", "AUTOCLICKER", "MEDIUM", f"name~{key}")
                else:
                    push(label, "AUTOCLICKER", "HIGH", f"name~{key}")
        for key, nkey, (label, sev) in _BYPASS_KEYS:
            if _key_matches(nkey, n) or _key_matches(key, fname_lower):
                if key in INFO_TOOL_KEYS:
                    push(f"{label} (ferramenta de análise/remoto)", "INFO", "LOW", f"name~{key}")
                else:
                    push(label, "BYPASS", sev, f"name~{key}")
    return hits


def detection_hits(filename: str):
    """scan_filename sem os itens informativos (ferramentas do staff / nome ambíguo de mod)."""
    return [h for h in scan_filename(filename) if h[1] != "INFO" and "confirmar conteúdo" not in h[3]]


def get_active_processes():
    procs = []
    for p in psutil.process_iter(["pid", "name", "exe"]):
        try:
            info = p.info
            procs.append((info.get("pid"), info.get("name") or "", info.get("exe") or ""))
        except Exception:
            continue
    return procs


LEGIT_AGENTS = ("authlib-injector", "optifine", "jvisualvm", "yourkit", "intellij", "idea_rt", "jacoco",
                "jrebel", "lunar", "feather", "badlion", "labymod", "essential", "forge", "fabric", "mixin",
                "sponge", "tlauncher", "ely.by", "newrelic", "datadog", "jmx", "prometheus", "spark",
                "neoforge", "quilt", "modrinth", "prism", "multimc", "polymc", "curseforge", "atlauncher",
                "sklauncher", "gdlauncher", "theseus", "lwjgl", "javaagent-all", "weave")
AGENT_CHEAT_WORDS = ("vape", "meteor", "sigma", "cheat", "hack", "ghost", "raven", "rise", "liquid",
                     "wurst", "argon", "drip", "dope", "clicker", "reach", "aura", "bypass", "loader")


def _is_minecraft_java(name, cmd):
    return ("java" in name or "minecraft" in name) and any(
        k in cmd for k in ("net.minecraft", "minecraft", "lunar", "badlion", "feather", "fabric",
                           "forge", "labymod", ".minecraft", "--gamedir", "--accesstoken", "--version"))


def scan_running_java_agents():
    """Processos Java do Minecraft com -javaagent fora da lista de agentes legítimos."""
    findings = []
    for p in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            name = (p.info.get("name") or "").lower()
            raw = p.info.get("cmdline") or []
            cmd = " ".join(raw).lower()
        except Exception:
            continue
        if "java" not in name and "minecraft" not in name:
            continue
        for arg in raw:
            if not arg.lower().startswith("-javaagent:"):
                continue
            agent = arg.split(":", 1)[1].split("=", 1)[0].strip('"')
            low = agent.lower()
            base = os.path.basename(low)
            if any(k in base for k in LEGIT_AGENTS) and not any(k in base for k in AGENT_CHEAT_WORDS):
                continue
            sev, evs = "MEDIUM", []
            if any(k in base for k in AGENT_CHEAT_WORDS):
                sev = "CRITICAL"
            if low.endswith(".jar") and os.path.isfile(agent):
                jsev, evs = deep_inspect_jar(agent)
                if jsev:
                    sev = jsev if SEV_RANK_E.get(jsev, 3) < SEV_RANK_E.get(sev, 3) else sev
            findings.append((p.info.get("pid"), agent, sev, (" | ".join(evs[:3]) or cmd[:200])))
    return findings


_SAFE_DLL_DIR_KEYS = ("\\windows\\", "\\program files", "\\programdata\\microsoft", "\\natives", "\\bin\\",
                      "\\.minecraft\\", "\\.lunarclient\\", "\\.feather\\", "\\.badlion\\", "\\java",
                      "\\jre", "\\jdk", "\\runtime\\", "\\nvidia", "\\steam", "\\discord", "\\obs",
                      "\\overwolf", "\\medal", "\\prismlauncher\\", "\\modrinthapp\\", "\\curseforge\\",
                      "\\microsoft\\", "\\amd\\", "\\intel\\", "\\.tlauncher\\", "\\gg.essential\\")
_SAFE_DLL_NAMES = ("lwjgl", "openal", "glfw", "jemalloc", "jinput", "discord", "jna", "jnidispatch",
                   "sqlite", "netty", "zstd", "lz4", "mcef", "graphics-hook", "gameoverlay", "rtsshooks",
                   "nvd3d", "nvoglv", "atio", "amdxx", "ig9icd", "ig75icd", "sodium", "vulkan", "opengl",
                   "imm32", "msvcp", "vcruntime", "ucrtbase", "api-ms-win", "steam", "obs-", "owclient",
                   "medal", "nahimic", "mcl", "sapi", "rendertoolkit", "fmod", "libwinpthread", "libgcc")


def scan_java_runtime():
    """Minecraft rodando AGORA: jars do classpath e DLLs carregadas fora do lugar (injeção)."""
    findings = []
    for p in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            name = (p.info.get("name") or "").lower()
            raw = p.info.get("cmdline") or []
            cmd = " ".join(raw).lower()
        except Exception:
            continue
        if not _is_minecraft_java(name, cmd):
            continue
        pid = p.info.get("pid")
        cp = ""
        for i, a in enumerate(raw):
            if a in ("-cp", "-classpath", "--class-path") and i + 1 < len(raw):
                cp = raw[i + 1]
        for entry in re.split(r"[;:](?![\\/])", cp):
            base = os.path.basename(entry.strip())
            for label, kind, sev, ev in detection_hits(base):
                findings.append(("Ameaças", {"name": f"{label} carregado no Minecraft (PID {pid})",
                                             "desc": "Jar de xit no classpath do jogo em execução — EM INSTÂNCIA.",
                                             "path": entry, "severity": "CRITICAL", "evidence": f"classpath:{base}"}))
        try:
            maps = p.memory_maps(grouped=True)
        except Exception:
            maps = []
        for m in maps:
            path = getattr(m, "path", "") or ""
            lp = path.lower()
            if not lp.endswith(".dll"):
                continue
            base = os.path.basename(lp)
            hits = detection_hits(base)
            if not hits and (any(k in lp for k in _SAFE_DLL_DIR_KEYS) or any(base.startswith(k) for k in _SAFE_DLL_NAMES)):
                continue
            esev, eev = deep_inspect_exe(path)
            sev = "CRITICAL" if hits else (esev or "MEDIUM")
            if not hits and not esev and not any(k in lp for k in ("\\temp\\", "\\downloads\\", "\\desktop\\", "\\appdata\\")):
                continue
            ev = ", ".join(h[0] for h in hits) or " | ".join(eev[:3]) or "DLL fora das pastas do Java/Windows/launcher"
            findings.append(("Ameaças", {"name": f"DLL injetada no Minecraft: {os.path.basename(path)}",
                                         "desc": f"DLL carregada dentro do javaw (PID {pid}) a partir de pasta incomum.",
                                         "path": path, "severity": sev, "evidence": ev}))
    return findings


def is_hidden(path: str) -> bool:
    try:
        name = os.path.basename(path)
        if name.startswith(".") and name not in (".", ".."):
            return True
        if os.name == "nt":
            import ctypes
            FILE_ATTRIBUTE_HIDDEN = 0x2
            attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))
            if attrs != -1 and (attrs & FILE_ATTRIBUTE_HIDDEN):
                return True
    except Exception:
        pass
    return False


def scan_recycle_bin():
    findings = []
    try:
        if os.name != "nt":
            return findings
        for drive_letter in [chr(65 + i) for i in range(26)]:
            root = f"{drive_letter}:\\$Recycle.Bin"
            if not os.path.isdir(root):
                continue
            try:
                sids = os.listdir(root)
            except Exception:
                continue
            for sid in sids:
                sid_dir = os.path.join(root, sid)
                if not os.path.isdir(sid_dir):
                    continue
                try:
                    entries = os.listdir(sid_dir)
                except Exception:
                    continue
                for entry in entries:
                    full = os.path.join(sid_dir, entry)
                    original_name = entry
                    if entry.startswith("$I") and os.path.isfile(full):
                        try:
                            with open(full, "rb") as f:
                                data = f.read()
                            for off in (28, 24):
                                if len(data) > off + 4:
                                    try:
                                        raw = data[off:].split(b"\x00\x00")[0] + b"\x00"
                                        original_name = raw.decode("utf-16-le", errors="ignore").strip("\x00") or entry
                                        if original_name:
                                            break
                                    except Exception:
                                        continue
                        except Exception:
                            pass
                    findings.append((original_name, full))
    except Exception:
        pass
    return findings


def scan_text_file(path: str, max_bytes: int = 512 * 1024, custom_strings=None):
    """Retorna (hits, forte). Ignora linhas de CHAT — alguém falar "vape" no chat não é xit."""
    hits = []
    strong = False
    custom_strings = custom_strings or []
    try:
        with open(path, "rb") as f:
            data = f.read(max_bytes)
        text = data.decode("utf-8", errors="ignore").lower()
        if _text_prefilter().search(text):
            rx = _text_prefilter()
            for line in text.splitlines():
                if len(line) > 2000 or not rx.search(line):
                    continue
                if "[chat]" in line or "[system]" in line or "<" in line[:80] and ">" in line[:120]:
                    continue
                for kw in TEXT_SUSPICIOUS_STRINGS:
                    if kw in line:
                        hits.append(kw)
                        if kw.startswith("-javaagent:") or _loaded_kw(line, kw) or \
                                re.search(re.escape(kw) + r'"?\s*[:=]\s*"?(?:true|on|1|enabled)\b', line):
                            strong = True
                for key, (label, sev) in CHEAT_CLIENTS.items():
                    if len(key) >= 8 and " " in key and key in line:
                        hits.append(f"{label} (menção)")
                        if _loaded_kw(line, key):
                            strong = True
                if len(hits) > 30:
                    break
        for cs in custom_strings:
            val = (cs.get("string") or "").strip().lower()
            if val and len(val) >= 4 and val in text:
                hits.append(f"{cs.get('client') or val} (custom)")
                strong = True
    except Exception:
        pass
    return list(dict.fromkeys(hits)), strong


def enumerate_hidden(paths, limit_per_root: int = 400):
    results = []
    for root_path in paths:
        if not os.path.exists(root_path):
            continue
        count = 0
        try:
            for root, dirs, files in os.walk(root_path):
                for d in list(dirs):
                    full = os.path.join(root, d)
                    if is_hidden(full):
                        results.append(("dir", full))
                        count += 1
                for f in files:
                    full = os.path.join(root, f)
                    if is_hidden(full):
                        results.append(("file", full))
                        count += 1
                    if count > limit_per_root:
                        break
                if count > limit_per_root:
                    break
        except Exception:
            continue
    return results


def play_alert_sound(critical: bool = False):
    try:
        if os.name != "nt":
            return
        import winsound
        if critical:
            for _ in range(3):
                winsound.Beep(1500, 120)
                time.sleep(0.05)
        else:
            winsound.Beep(800, 200)
    except Exception:
        pass


# ==============================================================================
#              ADMIN, USB, CLIPBOARD, INSPEÇÃO PROFUNDA JAR/EXE
# ==============================================================================

def is_admin() -> bool:
    try:
        if os.name == "nt":
            import ctypes
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        return os.geteuid() == 0
    except Exception:
        return False


def try_elevate_admin() -> bool:
    try:
        if os.name != "nt" or is_admin():
            return False
        import ctypes
        params = " ".join([f'"{a}"' for a in sys.argv])
        ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
        return int(ret) > 32
    except Exception:
        return False


def copy_to_clipboard(text: str) -> bool:
    try:
        import tkinter as tk
        r = tk.Tk()
        r.withdraw()
        r.clipboard_clear()
        r.clipboard_append(text)
        r.update()
        r.after(200, r.destroy)
        return True
    except Exception:
        pass
    try:
        if os.name == "nt":
            subprocess.run(["clip"], input=text.encode("utf-16-le"), check=False, timeout=3)
            return True
    except Exception:
        pass
    return False


def get_current_usb_devices():
    devices = []
    if os.name != "nt":
        return devices
    try:
        out = subprocess.run(
            ["wmic", "path", "Win32_PnPEntity", "where", "DeviceID like 'USB%'",
             "get", "Caption,DeviceID", "/format:csv"],
            capture_output=True, text=True, timeout=15)
        for line in out.stdout.splitlines():
            line = line.strip()
            if not line or line.lower().startswith("node") or "USB" not in line.upper():
                continue
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 3:
                caption = parts[1]
                device_id = parts[2]
                if caption and caption.lower() != "caption":
                    devices.append({"caption": caption, "device_id": device_id, "state": "CONECTADO"})
    except Exception:
        pass
    return devices


def get_usb_history():
    history = []
    if os.name != "nt":
        return history
    try:
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Enum\USBSTOR") as k:
                for i in range(0, 200):
                    try:
                        subname = winreg.EnumKey(k, i)
                    except OSError:
                        break
                    history.append({"type": "USBSTOR",
                                    "caption": subname.replace("&", " ").replace("_", " "),
                                    "device_id": subname, "state": "HISTÓRICO"})
        except FileNotFoundError:
            pass
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                r"Software\Microsoft\Windows\CurrentVersion\Explorer\MountPoints2") as k:
                idx = 0
                while idx < 500:
                    try:
                        subname = winreg.EnumKey(k, idx)
                    except OSError:
                        break
                    idx += 1
                    if subname.startswith("{") or "&" in subname or subname.startswith("#"):
                        history.append({"type": "MountPoint", "caption": subname,
                                        "device_id": subname, "state": "MONTADO RECENTEMENTE"})
        except FileNotFoundError:
            pass
    except Exception:
        pass
    try:
        setupapi_log = r"C:\Windows\INF\setupapi.dev.log"
        if os.path.exists(setupapi_log):
            with open(setupapi_log, "r", encoding="utf-8", errors="ignore") as f:
                try:
                    f.seek(-500 * 1024, 2)
                except Exception:
                    pass
                tail = f.read()
            usb_events = re.findall(
                r">>>\s+\[Device Install \(Hardware initiated\).*?USB.*?\](.*?)<<<", tail, re.DOTALL)
            for ev in usb_events[-20:]:
                m = re.search(r"Section start (\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}[^\r\n]*)", ev)
                ts = m.group(1) if m else "?"
                m2 = re.search(r"USB[\\/][A-Z0-9_&]+", ev)
                dev = m2.group(0) if m2 else "USB device"
                history.append({"type": "SetupAPI", "caption": f"{dev}",
                                "device_id": dev, "state": f"INSTALADO em {ts}"})
    except Exception:
        pass
    # RecentDocs + atalhos recentes apontando para drives removíveis
    try:
        import winreg
        ext_markers = (".jar", ".exe", ".dll", ".bat", ".ahk", ".zip", ".rar")
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                r"Software\Microsoft\Windows\CurrentVersion\Explorer\RecentDocs") as k:
                i = 0
                while i < 200:
                    try:
                        vname, vval, _ = winreg.EnumValue(k, i)
                    except OSError:
                        break
                    i += 1
                    try:
                        txt = bytes(vval).decode("utf-16-le", errors="ignore").split("\x00")[0]
                    except Exception:
                        continue
                    if txt and txt.lower().endswith(ext_markers):
                        history.append({"type": "RecentDocs", "caption": txt[:80],
                                        "device_id": txt, "state": "ABERTO RECENTEMENTE"})
        except FileNotFoundError:
            pass
    except Exception:
        pass
    try:
        recent = os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Recent")
        if os.path.isdir(recent):
            lnks = [os.path.join(recent, f) for f in os.listdir(recent) if f.lower().endswith(".lnk")]
            for lnk in lnks[:150]:
                try:
                    with open(lnk, "rb") as f:
                        blob = f.read(4096)
                    text = blob.decode("latin-1", errors="ignore")
                    m = re.search(r"([D-Zd-z]:\\[^\x00]{2,120})", text)
                    if m:
                        target = m.group(1).strip()
                        tl = target.lower()
                        if tl.endswith((".jar", ".exe", ".bat", ".ahk", ".dll")) or ":\\" in tl:
                            history.append({"type": "Atalho (.lnk)",
                                            "caption": os.path.basename(lnk).replace(".lnk", ""),
                                            "device_id": target, "state": "ATALHO RECENTE"})
                except Exception:
                    continue
    except Exception:
        pass
    return history


_KW_RE_CACHE = {}


def _kw_boundary_in_bytes(data: bytes, kw: str) -> bool:
    """Match de palavra em bytecode respeitando fronteira (anti-falso-positivo)."""
    rx = _KW_RE_CACHE.get(kw)
    if rx is None:
        try:
            rx = re.compile(rb"(?:^|[^a-z0-9])" + re.escape(kw.encode("latin-1")) + rb"(?:$|[^a-z0-9])")
        except Exception:
            rx = False
        _KW_RE_CACHE[kw] = rx
    if rx is False:
        return kw.encode("utf-8", "ignore") in data
    return bool(rx.search(data))


_PREFILTERS = {}



def _bytes_prefilter(name, words):
    """Regex única com todas as palavras: 1 passada no dado em vez de centenas."""
    rx = _PREFILTERS.get(name)
    if rx is None:
        ws = {(w.decode("latin-1") if isinstance(w, bytes) else w.encode("latin-1", "ignore").decode("latin-1")) for w in words if w}
        rx = re.compile(_trie_pattern(ws).encode("latin-1")) if ws else re.compile(b"(?!)")
        _PREFILTERS[name] = rx
    return rx


def _text_prefilter():
    rx = _PREFILTERS.get("text")
    if rx is None:
        ws = set(TEXT_SUSPICIOUS_STRINGS) | {k for k in CHEAT_CLIENTS if len(k) >= 8 and " " in k}
        rx = re.compile(_trie_pattern({w for w in ws if w}))
        _PREFILTERS["text"] = rx
    return rx


def deep_inspect_jar(jar_path, custom_strings=None, display_name=None):
    """Abre o .jar inteiro procurando xit. Retorna (severity, evidences).

    Aceita caminho ou arquivo em memória (jar dentro de .zip). Usa estrutura de
    módulos, ID do mod e bytecode; mods legítimos sem sinal forte são liberados.
    """
    evidences = []
    severity = None
    strong_hits = set()
    weak_hits = set()
    jar_name = display_name or (os.path.basename(jar_path) if isinstance(jar_path, str) else "mod.jar")
    try:
        with zipfile.ZipFile(jar_path, "r") as z:
            names = z.namelist()
            joined_lower = " ".join(names).lower()
            manifest = ""
            try:
                manifest = z.read("META-INF/MANIFEST.MF").decode("utf-8", errors="ignore")
            except Exception:
                pass

            # --- É um mod/lib legítimo? (maioria das classes em pacote conhecido) ---
            class_names = [n for n in names if n.endswith(".class")]
            legit_pkg_count = sum(1 for n in class_names
                                  if any(n.lower().startswith(p) for p in LEGIT_PACKAGE_PREFIXES))
            mostly_legit = bool(class_names) and (legit_pkg_count / max(1, len(class_names))) >= 0.80
            name_is_legit = is_legit_name(jar_name)

            has_premain = bool(re.search(r"Premain-Class\s*:", manifest, re.I))
            if has_premain:
                m = re.search(r"Premain-Class\s*:\s*([^\r\n]+)", manifest, re.I)
                pc = m.group(1).strip() if m else "?"
                # Agentes de profiling legítimos não contam
                if not any(k in pc.lower() for k in ("optifine", "jvisualvm", "yourkit", "intellij", "jacoco", "jrebel")):
                    evidences.append(f"Premain-Class: {pc} (Java Agent — injeção)")
                    has_premain = True
                else:
                    has_premain = False

            # --- Ofuscação pesada: só conta como sinal se NÃO for mod legítimo ---
            short_names = 0
            for cn in class_names:
                base = cn.rsplit("/", 1)[-1].replace(".class", "")
                if len(base) <= 2 and base.isalpha():
                    short_names += 1
            heavy_obf = False
            if class_names and not mostly_legit and not name_is_legit:
                ratio = short_names / len(class_names)
                if ratio >= 0.7 and len(class_names) >= 8:
                    heavy_obf = True
                    evidences.append(f"Ofuscação pesada: {short_names}/{len(class_names)} classes com nome curto")

            # --- Payload cifrado grande solto na raiz ---
            random_blobs = [n for n in names if "/" not in n and n and re.fullmatch(r"[A-Z0-9]{10,}", n)]
            big_blob = None
            for rb in random_blobs:
                try:
                    if z.getinfo(rb).file_size > 100_000:
                        big_blob = (rb, z.getinfo(rb).file_size)
                        break
                except Exception:
                    pass
            if big_blob:
                evidences.append(f"Payload cifrado: {big_blob[0]} ({big_blob[1]//1024}KB)")

            # --- Varredura de TODAS as classes (abre o jar inteiro) ---
            read_bytes = 0
            MAX_TOTAL = 24 * 1024 * 1024   # teto p/ não travar em jars gigantes
            MAX_PER = 384 * 1024
            custom_hits = []
            custom_strings = custom_strings or []
            jar_any_rx = _bytes_prefilter("jar", list(JAR_STRONG_KEYWORDS) + list(JAR_WEAK_KEYWORDS))
            for cn in class_names:
                if read_bytes > MAX_TOTAL:
                    break
                cl = cn.lower()
                # nome da classe/pacote já pode conter marca forte
                cbase = cl.rsplit("/", 1)[-1][:-6].split("$")[0]
                for kw in JAR_STRONG_KEYWORDS:
                    if "/" in kw:
                        if kw in cl:
                            strong_hits.add(kw)
                    elif cbase == kw or cbase in (kw + "module", kw + "hack", kw + "mod", kw + "feature"):
                        strong_hits.add(kw)
                try:
                    data = z.read(cn)[:MAX_PER]
                except Exception:
                    continue
                read_bytes += len(data)
                low = data.lower()
                for cs in custom_strings:
                    val = (cs.get("string") or "").strip().lower()
                    if val and len(val) >= 4 and val.encode("latin-1", "ignore") in low:
                        custom_hits.append(cs)
                # pré-filtro: a maioria das classes não tem nenhuma palavra -> pula o loop
                if not jar_any_rx.search(low):
                    continue
                for kw in JAR_STRONG_KEYWORDS:
                    if kw in strong_hits:
                        continue
                    if (b"/" in kw.encode() and kw.encode() in low) or _kw_boundary_in_bytes(low, kw):
                        strong_hits.add(kw)
                for kw in JAR_WEAK_KEYWORDS:
                    if kw in weak_hits:
                        continue
                    if _kw_boundary_in_bytes(low, kw):
                        weak_hits.add(kw)

            # também checa marcas fortes nos nomes de arquivos (recursos, libs)
            for kw in JAR_STRONG_KEYWORDS:
                if "/" in kw and kw not in strong_hits and kw in joined_lower:
                    strong_hits.add(kw)

            if strong_hits:
                evidences.append("Módulos de xit: " + ", ".join(sorted(strong_hits)[:8]))

            # --- Estrutura de hack client: .../module/combat/KillAura.class etc. ---
            module_hits = set()
            cat_dirs = set()
            for cn in class_names:
                cl = "/" + cn.lower()
                base = cl.rsplit("/", 1)[-1][:-6].split("$")[0]
                parts = cl.split("/")
                in_mod_dir = bool(_MODULE_DIR_RE.search(cl))
                cats = _MODULE_CATS.intersection(parts[:-1])
                if (in_mod_dir or cats) and base in CHEAT_MODULE_NAMES:
                    module_hits.add(base)
                    cat_dirs.update(cats)
            module_struct = len(module_hits) >= 4 or (len(module_hits) >= 3 and len(cat_dirs) >= 2)
            if module_struct:
                evidences.append(f"Estrutura de hack client ({len(module_hits)} módulos): " +
                                 ", ".join(sorted(module_hits)[:8]))

            # --- ID declarado do mod (fabric.mod.json / mods.toml / quilt) ---
            mod_ids = set()
            for meta_name in ("fabric.mod.json", "quilt.mod.json", "META-INF/mods.toml", "META-INF/neoforge.mods.toml"):
                if meta_name in names:
                    try:
                        raw = z.read(meta_name)[:200_000].decode("utf-8", errors="ignore").lower()
                    except Exception:
                        continue
                    if meta_name.endswith(".json"):
                        m_id = re.search(r'^\s*\{\s*(?:[^{}]*?,\s*)?"id"\s*:\s*"([a-z0-9_\-\.]+)"', raw, re.S)
                        if not m_id:
                            m_id = re.search(r'"id"\s*:\s*"([a-z0-9_\-\.]+)"', raw.split('"depends"')[0].split('"custom"')[0])
                        if m_id:
                            mod_ids.add(m_id.group(1))
                    else:
                        mods_block = raw.split("[[dependencies")[0]
                        mod_ids.update(re.findall(r'modid\s*=\s*"([a-z0-9_\-\.]+)"', mods_block))
            mod_id_hit = None
            for mid in mod_ids:
                if mid in CHEAT_MOD_IDS:
                    mod_id_hit = CHEAT_MOD_IDS[mid]
                    evidences.append(f"ID do mod é de xit/vantagem: '{mid}' ({mod_id_hit[0]})")
                    break
            # fracas só valem em conjunto e fora de mod legítimo
            weak_valid = (len(weak_hits) >= 2) and not mostly_legit and not name_is_legit
            if weak_valid:
                evidences.append("Sinais fracos combinados: " + ", ".join(sorted(weak_hits)[:6]))

            if custom_hits:
                labels = list({(c.get("client") or c.get("string")) for c in custom_hits})[:5]
                evidences.append("String personalizada encontrada: " + ", ".join(labels))

            # --- Biblioteca nativa embutida (padrão Echo/MonoEcho loader.jar) ---
            native_libs = [n for n in names if n.lower().endswith(NATIVE_LIB_MARKERS)]
            native_evidence = bool(native_libs) and not mostly_legit and (heavy_obf or has_premain or bool(big_blob))
            if native_evidence:
                evidences.append("Biblioteca nativa embutida: " +
                                 ", ".join(os.path.basename(x) for x in native_libs[:3]) +
                                 " (xit carrega código nativo)")

            # --- Multi-loader disfarçado ---
            loader_kinds = set()
            if "fabric.mod.json" in names:
                loader_kinds.add("Fabric")
            if "META-INF/mods.toml" in names or "mcmod.info" in names:
                loader_kinds.add("Forge")
            if re.search(r"Main-Class\s*:", manifest, re.I):
                loader_kinds.add("Main-Class")
            if has_premain:
                loader_kinds.add("Java-Agent")
            meta_blob = manifest.lower()
            for jn in [n for n in names if n.lower().endswith((".json", ".toml", ".info")) and "/" not in n][:10]:
                try:
                    c = z.read(jn).decode("utf-8", errors="ignore").lower()
                    meta_blob += " " + c
                    if "labymod" in c or '"mainclass"' in c:
                        loader_kinds.add("LabyMod")
                except Exception:
                    continue
            multi_loader = len(loader_kinds) >= 3 and not mostly_legit
            if multi_loader:
                evidences.append("Multi-loader disfarçado: " + ", ".join(sorted(loader_kinds)) +
                                 " no mesmo .jar")

            # --- Metadados citando xit conhecido ---
            meta_cite = False
            for key, (label, sev) in CHEAT_CLIENTS.items():
                if len(key) >= 5 and key in meta_blob and key not in joined_lower:
                    evidences.append(f"Metadado cita xit conhecido: {label}")
                    meta_cite = True
                    break

            # --- Payload sem extensão grande carregado via código ---
            blob_files = []
            for n in names:
                if n.endswith("/") or n.endswith(".class"):
                    continue
                base = n.rsplit("/", 1)[-1]
                if base and "." not in base:
                    try:
                        sz = z.getinfo(n).file_size
                    except Exception:
                        sz = 0
                    if sz > 80_000:
                        blob_files.append((n, sz))
            code_payload = bool(blob_files) and not mostly_legit
            if code_payload:
                big = max(blob_files, key=lambda x: x[1])
                evidences.append(f"Payload sem extensão via código: {big[0]} ({big[1]//1024}KB)")

            # ---------------- Decisão de gravidade (conservadora) ----------------
            legit_ctx = mostly_legit or name_is_legit
            strong_signal = bool(has_premain or native_evidence or multi_loader or meta_cite or module_struct
                                 or big_blob or code_payload or len(strong_hits) >= 2 or custom_hits or mod_id_hit)
            if module_struct or custom_hits or meta_cite or len(strong_hits) >= 2:
                severity = "CRITICAL"
            elif strong_hits:
                # 1 única palavra forte: crítico só se o jar não parece mod legítimo
                severity = "MEDIUM" if legit_ctx else "HIGH"
            elif has_premain and (native_evidence or len(evidences) >= 2):
                severity = "CRITICAL"
            elif native_evidence or multi_loader or big_blob or code_payload:
                severity = "HIGH" if (len(evidences) >= 2 or heavy_obf) else "MEDIUM"
            elif weak_valid and heavy_obf:
                severity = "MEDIUM"
            else:
                severity = None
            if legit_ctx and severity and not (module_struct or custom_hits or meta_cite):
                severity = "MEDIUM"  # mod com nome/pacote legítimo: só revisar
            if mod_id_hit:
                severity = worst_sev(severity, mod_id_hit[1])

            # Rede de segurança final: mod legítimo sem sinal forte => liberado
            if legit_ctx and not strong_signal and not strong_hits:
                severity = None
    except zipfile.BadZipFile:
        return None, []
    except Exception:
        pass
    return severity, evidences


EXE_SIGNATURES = [
    # (assinatura, rótulo, peso)  — peso 3 = prova forte, 1 = só soma com outros sinais
    ("##var::clicker::i_send_input_method", "Autoclicker (assinatura Rust/ImGui)", 4),
    ("Only MC\x00inputs", "Autoclicker Minecraft (Only MC)", 4),
    ("##var::clicker", "Autoclicker (padrão ##var::clicker)", 4),
    ("mouse_event\x00PostMessage\x00SendNotifyMessage", "Autoclicker (3 métodos de input)", 3),
    ("dllinject", "DLL Injector", 3),
    ("CE_MEMSCAN", "Cheat Engine plugin", 4),
    ("SpooferPro", "HWID Spoofer", 4),
    ("hwid_spoof", "HWID Spoofer", 4),
    ("frida-agent", "Frida injector", 3),
    ("ManualMap", "Manual Map Injector", 2),
    ("self_destruct", "Rotina self-destruct", 2),
    ("selfdestruct", "Rotina self-destruct", 2),
    ("clicker::", "Autoclicker (namespace clicker::)", 3),
    ("jitter_click", "Autoclicker (jitter)", 3),
    ("jitterclick", "Autoclicker (jitter)", 3),
    ("butterfly_click", "Autoclicker (butterfly)", 3),
    ("kdmapper", "KDMapper (driver mapper)", 4),
    ("autoclicker", "String 'autoclicker'", 2),
    ("auto clicker", "String 'auto clicker'", 2),
    ("clicks per second", "Configuração de CPS", 2),
    ("min_cps", "Configuração min_cps", 2),
    ("max_cps", "Configuração max_cps", 2),
    ("cps_min", "Configuração cps_min", 2),
    ("cps_max", "Configuração cps_max", 2),
    ("right clicker", "Right clicker", 2),
    ("left clicker", "Left clicker", 2),
    ("self destruct", "Self-destruct na interface", 2),
    ("destruct", "Opção destruct", 1),
    ("LWJGL", "Referência LWJGL (Minecraft)", 1),
    ("javaw.exe", "Mira o processo javaw.exe", 1),
    ("JNI_GetCreatedJavaVMs", "Acessa a JVM por fora (JNI_GetCreatedJavaVMs)", 2),
    ("JVMTI", "JVMTI (instrumentação da JVM)", 1),
    ("SetWindowsHookEx", "Hook global de mouse/teclado", 1),
    ("SendInput", "Envio de input sintético", 1),
    ("mouse_event", "Envio de clique sintético", 1),
    ("CreateRemoteThread", "Thread remota", 1),
    ("WriteProcessMemory", "Escrita em memória de outro processo", 1),
    ("VirtualAllocEx", "Alocação em outro processo", 1),
    ("NtCreateThreadEx", "NtCreateThreadEx", 1),
    ("LWJGL Display", "Janela do Minecraft (LWJGL Display)", 2),
    ("GLFW30", "Janela do Minecraft (GLFW30)", 2),
    ("AutoHotkeyGUI", "AutoHotkey compilado", 2),
    (">AUTOHOTKEY SCRIPT<", "AutoHotkey compilado", 2),
]
_EXE_GENERIC_CLIENTS = {"matrix client", "photon client", "fusion client", "cosmos client", "eclipse client",
                        "comet client", "atomic client", "ambient client", "snow client", "swift client",
                        "omega client", "nitro client", "polar client", "lambda client", "venom client",
                        "vega client", "impact client", "future client", "moon client", "flux client",
                        "exhibition", "ghost client", "ghostclient", "cracked client", "skid client",
                        "lucid client", "remix client", "breeze client", "taco client", "keystone client"}
_EXE_CLIENT_KEYS = [k for k in CHEAT_CLIENTS
                    if (len(k) >= 7 and " " in k or len(k) >= 9) and k not in _EXE_GENERIC_CLIENTS]


def pe_company(data: bytes) -> str:
    m = _VENDOR_RE.search(data)
    if not m:
        return ""
    return m.group(1).replace(b"\x00", b"").decode("latin-1", "ignore").strip()


def deep_inspect_exe(exe_path: str, max_bytes: int = 6 * 1024 * 1024):
    """Pontua sinais no binário. Só marca com prova forte (anti-falso-positivo).

    APIs de injeção/hook sozinhas NÃO marcam (Discord, OBS e antivírus usam).
    Elas só contam quando o binário também mira o Minecraft ou tem cara de clicker.
    """
    evidences = []
    try:
        size = os.path.getsize(exe_path)
        if size > 200 * 1024 * 1024 or size < 2048:
            return None, []
        with open(exe_path, "rb") as f:
            data = f.read(min(size, max_bytes))
            if size > max_bytes:  # tabela de recursos (versão/empresa) costuma ficar no fim
                f.seek(max(0, size - 512 * 1024))
                data += f.read()
        if data[:2] != b"MZ":
            return None, []
        company = pe_company(data)
        trusted = company and any(v.decode().lower() in company.lower() for v in TRUSTED_VENDORS)
        low = data.lower()
        score, strong, hard = 0, 0, 0
        injection = 0
        mc_target = False
        clicker = 0
        if _bytes_prefilter("exe", [sg.lower() for sg, _, _ in EXE_SIGNATURES]).search(low):
            for sig, label, w in EXE_SIGNATURES:
                if sig.lower().encode("latin-1", errors="ignore") in low:
                    if w >= 2:
                        evidences.append(f"Assinatura: {label}")
                    score += w
                    if w >= 3:
                        strong += 1
                    if w >= 4:
                        hard += 1
                    if sig in ("CreateRemoteThread", "WriteProcessMemory", "VirtualAllocEx", "NtCreateThreadEx"):
                        injection += 1
                    if sig in ("javaw.exe", "LWJGL", "LWJGL Display", "GLFW30", "JNI_GetCreatedJavaVMs", "JVMTI"):
                        mc_target = True
                    if "cps" in sig.lower() or "click" in sig.lower():
                        clicker += 1
        # nome de cliente de xit embutido no binário
        client_rx = _bytes_prefilter("exe_clients", _EXE_CLIENT_KEYS)
        m = client_rx.search(low)
        if m:
            evidences.append(f"Cita cliente de xit: {m.group(0).decode('latin-1', 'ignore')}")
            score += 3
            strong += 1
        launcher = any(k in os.path.basename(exe_path).lower() for k in (
            "prism", "multimc", "polymc", "sklauncher", "tlauncher", "modrinth", "curseforge", "lunar",
            "badlion", "feather", "atlauncher", "gdlauncher", "minecraft", "labymod", "technic"))
        if injection >= 3 and mc_target and not launcher and not trusted:
            evidences.append("Injetor mirando o Minecraft/JVM (thread remota + escrita de memória)")
            score += 4
            strong += 1
        if clicker >= 2 and (b"sendinput" in low or b"mouse_event" in low or b"postmessage" in low):
            evidences.append("Autoclicker: config de CPS/clique + envio de clique sintético")
            score += 2
            strong += 1
        if b"UPX0" in data[:4096] and (clicker or mc_target):
            evidences.append("Compactado com UPX + strings de clicker/Minecraft")
            score += 1
        if trusted and not m and not hard and clicker < 2:
            return None, []
        if strong == 0 or score < 3:
            return None, []
        severity = "CRITICAL" if score >= 6 else ("HIGH" if score >= 4 else "MEDIUM")
        if company:
            evidences.append(f"Empresa no binário: {company[:40]}")
        return severity, evidences
    except Exception:
        return None, []


_RAR_NAME_RE = re.compile(rb"[\w\-\. \+\(\)\[\]!@#&]{2,90}\.(?:jar|exe|dll|bat|cmd|ahk|ps1|vbs)", re.I)


def inspect_archive(path: str, custom_strings=None):
    """.zip/.rar/.7z: procura xit nos nomes de dentro e analisa os .jar/.exe internos (zip)."""
    evidences, sev = [], None
    low = path.lower()
    try:
        if low.endswith(".zip"):
            with zipfile.ZipFile(path) as z:
                if "pack.mcmeta" in z.namelist():  # é um texture pack (mesmo fora de resourcepacks)
                    psev, pev = inspect_pack(path)
                    if psev:
                        evidences.extend(f"Texture pack ilegal: {e}" for e in pev)
                        sev = worst_sev(sev, psev)
                infos = z.infolist()[:4000]
                deep_budget = 3
                for info in infos:
                    inner = info.filename
                    base = inner.rsplit("/", 1)[-1]
                    for label, kind, s, ev in detection_hits(base):
                        if s == "LOW":
                            continue
                        evidences.append(f"Contém '{base}' → {label}")
                        sev = worst_sev(sev, s)
                    il = base.lower()
                    if deep_budget and il.endswith(".jar") and 0 < info.file_size < 16 * 1024 * 1024:
                        deep_budget -= 1
                        try:
                            jsev, jev = deep_inspect_jar(BytesIO(z.read(info)), custom_strings, display_name=base)
                        except Exception:
                            jsev, jev = None, []
                        if jsev:
                            evidences.append(f"{base}: " + " | ".join(jev[:2]))
                            sev = worst_sev(sev, jsev)
                    if len(evidences) > 12:
                        break
        else:
            with open(path, "rb") as f:
                data = f.read(4 * 1024 * 1024)
            seen = set()
            for m in _RAR_NAME_RE.finditer(data):
                base = os.path.basename(m.group(0).decode("latin-1", "ignore").replace("\\", "/").strip())
                if base.lower() in seen:
                    continue
                seen.add(base.lower())
                for label, kind, s, ev in detection_hits(base):
                    if s == "LOW":
                        continue
                    evidences.append(f"Contém '{base}' → {label}")
                    sev = worst_sev(sev, s)
                if len(seen) > 3000 or len(evidences) > 12:
                    break
    except Exception:
        pass
    return sev, list(dict.fromkeys(evidences))


SCRIPT_SIGNATURES = [
    (r"fsutil\s+usn\s+deletejournal", "Apaga o USN Journal (bypass)", "CRITICAL", "BYPASS"),
    (r"wevtutil(?:\.exe)?\s+cl\b", "Limpa o Event Log (bypass)", "CRITICAL", "BYPASS"),
    (r"clear-eventlog", "Limpa o Event Log (bypass)", "CRITICAL", "BYPASS"),
    (r"(?:del|erase|remove-item|rd|rmdir)\b[^\n]{0,80}\\prefetch", "Apaga o Prefetch (bypass)", "CRITICAL", "BYPASS"),
    (r"reg(?:\.exe)?\s+delete[^\n]{0,160}(?:\\bam\\|userassist|shellbags?|bagmru|muicache|recentdocs|runmru|appcompatcache)",
     "Apaga rastros no Registro (BAM/UserAssist/ShellBags)", "CRITICAL", "BYPASS"),
    (r"remove-itemproperty[^\n]{0,160}(?:userassist|bam|muicache|bagmru)", "Apaga rastros no Registro", "CRITICAL", "BYPASS"),
    (r"(?:del|erase|remove-item)\b[^\n]{0,80}(?:\\recent\\|automaticdestinations|jumplist)", "Apaga histórico recente (bypass)", "HIGH", "BYPASS"),
    (r"-javaagent:", "Injeta Java Agent no jogo", "HIGH", "CHEAT"),
    (r"\b(?:loop|while)\b[\s\S]{0,400}?\b(?:click|mouseclick|controlclick|send(?:input|play|event)?\s*,?\s*\{?(?:l|r)button)",
     "Macro de clique em loop (autoclicker)", "CRITICAL", "AUTOCLICKER"),
    (r"(?:pyautogui|pynput|mouse\.click|win32api\.mouse_event|ctypes\.windll\.user32\.(?:mouse_event|sendinput))",
     "Script de clique automático (Python)", "HIGH", "AUTOCLICKER"),
    (r"\b(?:cps|clicks?\s*per\s*second)\b", "Configura CPS", "MEDIUM", "AUTOCLICKER"),
]
_SCRIPT_RES = [(re.compile(rx, re.I), lbl, sev, kind) for rx, lbl, sev, kind in SCRIPT_SIGNATURES]


_AHK_CLICK_RE = re.compile(r"\b(?:loop|while|settimer)\b[\s\S]{0,400}?(?:^|[\s,{])(?:click\b|mouseclick\b|controlclick\b|"
                           r"send(?:input|play|event)?\s*,?\s*\{(?:l|r)button)", re.I | re.M)
_PY_CLICK_RE = re.compile(r"(?:pyautogui\.click|mouse\.click|win32api\.mouse_event|user32\.(?:mouse_event|sendinput)|"
                          r"pynput[\s\S]{0,200}?\.click)", re.I)
_PY_LOOP_RE = re.compile(r"\b(?:while\s+true|while\s+1|for\s+\w+\s+in\s+range)\b[\s\S]{0,400}?(?:sleep|cps)", re.I)


def inspect_script(path: str):
    """Scripts .bat/.ps1/.vbs/.ahk/.py: macros de clique e comandos que apagam rastros."""
    hits = []
    ext = os.path.splitext(path)[1].lower()
    try:
        with open(path, "rb") as f:
            text = f.read(512 * 1024).decode("utf-8", errors="ignore")
            if "\x00" in text[:200]:
                text = text.replace("\x00", "")
    except Exception:
        return hits
    if "SCRIPT_SIGNATURES" in text and "Celestial" in text:
        return hits  # é o próprio scanner
    for rx, lbl, sev, kind in _SCRIPT_RES:
        if kind == "AUTOCLICKER":
            continue
        if rx.search(text):
            hits.append((lbl, sev, kind))
    if ext == ".ahk" and _AHK_CLICK_RE.search(text):
        hits.append(("Macro de clique em loop (autoclicker AHK)", "CRITICAL", "AUTOCLICKER"))
    elif ext in (".py", ".pyw") and _PY_CLICK_RE.search(text) and _PY_LOOP_RE.search(text):
        hits.append(("Script de clique automático em loop (Python)", "HIGH", "AUTOCLICKER"))
    elif ext in (".ps1", ".vbs") and re.search(r"mouse_event|sendinput|leftclick", text, re.I) and \
            re.search(r"\b(?:while|do|for)\b", text, re.I):
        hits.append(("Clique automático via script", "HIGH", "AUTOCLICKER"))
    return hits


def get_logon_time():
    """Início da sessão do usuário (logon). Fallback: horário de boot."""
    try:
        me = (_safe_user() or "").lower()
        starts = [u.started for u in psutil.users() if u.started and (not me or (u.name or "").lower() == me)]
        if starts:
            return min(starts)
    except Exception:
        pass
    try:
        return psutil.boot_time()
    except Exception:
        return 0


def instance_tag(ts, logon):
    if not ts or not logon:
        return "", True
    when = datetime.fromtimestamp(ts).strftime("%d/%m %H:%M")
    if ts >= logon:
        return f"EM INSTÂNCIA (executado {when}, depois do logon)", True
    return f"FORA DE INSTÂNCIA (executado {when}, antes do logon)", False


def file_status(path: str) -> str:
    try:
        return "Ativo" if os.path.exists(path) else "Excluído"
    except Exception:
        return "Desconhecido"


def file_meta(path: str):
    """Retorna (data_modificacao, tamanho_legivel) de um arquivo, se existir."""
    try:
        st = os.stat(path)
        dt = datetime.fromtimestamp(st.st_mtime).strftime("%d/%m/%Y %H:%M")
        size = st.st_size
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024 or unit == "GB":
                human = f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
                break
            size /= 1024.0
        return dt, human
    except Exception:
        return "—", "—"


def path_exists(path: str) -> bool:
    try:
        return bool(path) and os.path.exists(path)
    except Exception:
        return False


def open_in_explorer(path: str):
    """Abre o Explorer com o arquivo já selecionado (ou a pasta, se o arquivo sumiu)."""
    try:
        if not path:
            return False
        p = os.path.normpath(path)
        if os.name == "nt":
            if os.path.exists(p):
                subprocess.Popen(f'explorer /select,"{p}"')
                return True
            folder = os.path.dirname(p)
            if os.path.isdir(folder):
                os.startfile(folder)
                return True
            return False
        folder = p if os.path.isdir(p) else os.path.dirname(p)
        if os.path.isdir(folder):
            subprocess.Popen(["xdg-open", folder])
            return True
    except Exception:
        pass
    return False


def open_file_default(path: str) -> bool:
    """Abre o arquivo com o programa padrão do sistema (pode EXECUTAR o arquivo)."""
    try:
        if not path_exists(path):
            return False
        p = os.path.normpath(path)
        if os.name == "nt":
            os.startfile(p)
        else:
            subprocess.Popen(["xdg-open", p])
        return True
    except Exception:
        return False


def send_webhook(report: dict):
    try:
        detections = report.get("detections", [])
        user = report.get("user", "?")
        machine = report.get("machine", "?")
        os_info = report.get("os", "?")
        scanned = report.get("scanned", 0)
        elapsed = report.get("elapsed", 0)
        by_sev = {"CRITICAL": [], "HIGH": [], "MEDIUM": [], "LOW": []}
        for d in detections:
            by_sev.setdefault(d.get("severity", "LOW"), []).append(d)
        crit_n = len(by_sev.get("CRITICAL", []))
        if not detections:
            status, color = "🟢 LIMPO", 0x22DD99
        elif crit_n > 0:
            status, color = "🔴 XIT ENCONTRADO", 0xFF3B5C
        else:
            status, color = "🟠 SUSPEITO", 0xFF8A00
        # resumo por categoria
        by_cat = report.get("by_category", {})
        cat_summary = "  ".join(f"{c}: `{n}`" for c, n in by_cat.items() if n) or "—"
        top_reason = report.get("top_reason", "")
        fields = []
        for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            items = by_sev.get(sev, [])
            if not items:
                continue
            names = list({d["name"] for d in items})[:12]
            value = "\n".join(f"• `{n}`" for n in names)
            if len(items) > 12:
                value += f"\n_e mais {len(items) - 12}..._"
            fields.append({"name": f"{sev} ({len(items)})", "value": value[:1024], "inline": False})
        desc = f"**Status:** {status}\n**Detecções totais:** `{len(detections)}`"
        if top_reason:
            desc += f"\n**Motivo principal:** `{top_reason}`"
        desc += f"\n**Por categoria:** {cat_summary}"
        embed = {
            "title": f"{APP_NAME} {VERSION} — Relatório Forense",
            "description": desc,
            "color": color,
            "fields": [
                {"name": "👤 Usuário", "value": f"`{user}`", "inline": True},
                {"name": "🖥️ Máquina", "value": f"`{machine}`", "inline": True},
                {"name": "🪟 Sistema", "value": f"`{os_info}`", "inline": True},
                {"name": "📊 Arquivos", "value": f"`{scanned}`", "inline": True},
                {"name": "⏱️ Duração", "value": f"`{elapsed}s`", "inline": True},
                {"name": "📅 Data", "value": f"`{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}`", "inline": True},
            ] + fields,
            "footer": {"text": f"{APP_NAME} {VERSION} • Celestial Forensics"},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        payload = {"username": APP_NAME, "embeds": [embed]}
        requests.post(WEBHOOK_URL, json=payload, timeout=8)
    except Exception:
        pass


def _safe_user():
    try:
        return os.getlogin()
    except Exception:
        return os.environ.get("USER") or os.environ.get("USERNAME") or "Guest"


# ==============================================================================
#            STRINGS PERSONALIZADAS + HASHES (String Extractor)
# ==============================================================================

def _custom_strings_path() -> str:
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    folder = os.path.join(base, "CelestialScanner")
    try:
        os.makedirs(folder, exist_ok=True)
    except Exception:
        folder = os.path.expanduser("~")
    return os.path.join(folder, "custom_strings.json")


def load_custom_strings():
    """Lista de dicts: {process, client, string, severity}."""
    path = _custom_strings_path()
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                out = []
                for d in data:
                    if isinstance(d, dict) and d.get("string"):
                        out.append({
                            "process": d.get("process", "").strip(),
                            "client": d.get("client", "").strip(),
                            "string": d.get("string", "").strip(),
                            "severity": (d.get("severity") or "HIGH").upper(),
                        })
                return out
    except Exception:
        pass
    return []


def save_custom_strings(items) -> bool:
    try:
        with open(_custom_strings_path(), "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def parse_old_strings_format(raw: str):
    """Converte 'clientName:StringValue' (uma por linha) em dicts JSON."""
    out = []
    for line in (raw or "").splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        client, _, value = line.partition(":")
        client = client.strip()
        value = value.strip()
        if value:
            out.append({"process": "", "client": client, "string": value, "severity": "HIGH"})
    return out


def compute_hashes(path: str, max_bytes: int = 256 * 1024 * 1024):
    """Retorna (md5, sha256, size_bytes) de um arquivo."""
    import hashlib
    md5 = hashlib.md5()
    sha = hashlib.sha256()
    size = 0
    try:
        with open(path, "rb") as f:
            while True:
                chunk = f.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                md5.update(chunk)
                sha.update(chunk)
                if size > max_bytes:
                    break
        return md5.hexdigest(), sha.hexdigest(), size
    except Exception:
        return "—", "—", 0


def extract_ascii_strings(path: str, min_len: int = 5, max_bytes: int = 12 * 1024 * 1024, limit: int = 60000):
    """Extrai strings ASCII/UTF-16 imprimíveis de um binário (.exe/.dll/.jar)."""
    results = []
    try:
        with open(path, "rb") as f:
            data = f.read(max_bytes)
        for pat in (rb"[\x20-\x7e]{%d,}" % min_len,
                    rb"(?:[\x20-\x7e]\x00){%d,}" % min_len):
            for m in re.finditer(pat, data):
                s = m.group().replace(b"\x00", b"").decode("latin-1", "ignore").strip()
                if s:
                    results.append(s)
                if len(results) >= limit:
                    return results
    except Exception:
        pass
    return results


def analyze_single_file(path: str, custom_strings=None):
    """Análise forense de UM arquivo (String Extractor). Retorna dict completo."""
    custom_strings = custom_strings or []
    name = os.path.basename(path)
    low = name.lower()
    md5, sha256, size = compute_hashes(path)
    dt, human = file_meta(path)
    detections = []

    def add(label, sev, evidence, kind="CHEAT"):
        detections.append({"name": label, "severity": sev, "evidence": evidence, "kind": kind})

    for label, kind, sev, ev in scan_filename(name, require_strict=False):
        add(label, sev, f"nome: {ev}", kind)

    suspicious_count = 0
    if low.endswith(".jar"):
        sev, evs = deep_inspect_jar(path, custom_strings=custom_strings)
        if sev:
            for e in evs:
                add(f"JAR: {e[:60]}", sev, e)
        suspicious_count += len(evs)
    elif low.endswith((".exe", ".dll", ".scr", ".sys")):
        sev, evs = deep_inspect_exe(path)
        if sev:
            for e in evs:
                add(f"EXE: {e[:60]}", sev, e)
        suspicious_count += len(evs)
    elif low.endswith(ARCHIVE_EXTS):
        sev, evs = inspect_archive(path, custom_strings)
        for e in evs:
            add(f"Compactado: {e[:60]}", sev or "MEDIUM", e)
    if low.endswith(SCRIPT_EXTS):
        for lbl, sev, kind in inspect_script(path):
            add(f"Script: {lbl}", sev, lbl, kind)

    # strings extraídas + match com base + personalizadas
    strings = extract_ascii_strings(path) if size < 60 * 1024 * 1024 else []
    joined = "\n".join(strings).lower()
    matched_db = []
    for key in _EXE_CLIENT_KEYS:
        if key in joined:
            label, sev = CHEAT_CLIENTS[key]
            matched_db.append((label, sev, key))
    for label, sev, key in matched_db[:30]:
        add(f"String de xit: {label}", sev, f"string~{key}")
    for cs in custom_strings:
        val = (cs.get("string") or "").strip().lower()
        if val and len(val) >= 3 and val in joined:
            add(f"String personalizada: {cs.get('client') or val}", cs.get("severity", "HIGH"),
                f"custom~{val}")

    # veredito
    sev_rank = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    worst = min([sev_rank.get(d["severity"], 3) for d in detections], default=99)
    if worst == 0:
        verdict, vcolor = "DETECTADO", SEV_CRITICAL
    elif worst <= 2:
        verdict, vcolor = "SUSPEITO", SEV_HIGH
    elif detections:
        verdict, vcolor = "REVISAR", SEV_MEDIUM
    else:
        verdict, vcolor = "LIMPO", SEV_OK

    return {
        "name": name, "path": path, "md5": md5, "sha256": sha256,
        "size_h": human, "modified": dt, "detections": detections,
        "strings_total": len(strings), "verdict": verdict, "vcolor": vcolor,
    }


def scan_processes_for_strings(custom_strings=None):
    """Detecção de presença: casa processos vivos com base + strings custom."""
    custom_strings = custom_strings or []
    out = []
    for pid, name, exe in get_active_processes():
        nlow = (name + " " + (exe or "")).lower()
        if is_legit_name(name):
            continue
        for label, kind, sev, ev in detection_hits(name):
            out.append({"pid": pid, "name": name, "label": label, "severity": sev, "kind": kind})
        for cs in custom_strings:
            proc = (cs.get("process") or "").strip().lower()
            val = (cs.get("string") or "").strip().lower()
            if proc and proc not in nlow:
                continue
            if val and val in nlow:
                out.append({"pid": pid, "name": name,
                            "label": cs.get("client") or val,
                            "severity": cs.get("severity", "HIGH"), "kind": "CUSTOM"})
    return out




# ==============================================================================
#        MOTOR DE SCAN — roda em PROCESSO SEPARADO (a interface nunca trava)
# ==============================================================================
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED

SCAN_SKIP_DIRS = {"$recycle.bin", "system volume information", "windows.old", "node_modules",
                  ".git", ".cache", "gradle", "cache", "temp internet files", "inetcache",
                  "winsxs", "servicing", "driverstore", "$winreagent", "$windows.~bt", "$windows.~ws",
                  "softwaredistribution", "assembly", "__pycache__", ".gradle", ".m2", ".npm",
                  "windowsapps", "steamapps", "code cache", "gpucache", "cache_data", "service worker",
                  "indexeddb", "shadercache", "dxcache", "glcache", "webcache", "site-packages",
                  "$sysreset", "recovery", "msocache", "packages", "crashpad", "nvidia corporation",
                  "windows defender", "windows kits", "microsoft visual studio", "dotnet", "miktex"}
MAX_FILES = 900_000
TOTAL_EST = 250_000
_FILE_ATTRIBUTE_HIDDEN = 0x2
_FILE_ATTRIBUTE_REPARSE = 0x400
# Pastas de Minecraft/launchers: aqui textos, jars e ocultos recebem atenção total
MC_PATH_KEYS = ("\\.minecraft", "/.minecraft", "\\.lunarclient", "\\.badlion", "\\.feather", "prismlauncher",
                "multimc", "polymc", "\\.tlauncher", "modrinthapp", "com.modrinth", "\\curseforge\\minecraft",
                "\\.technic", "gg.essential", "atlauncher", "gdlauncher", "\\.sklauncher", "lunarclient",
                "badlion client", "\\labymod", "\\instances\\")
_EXE_SKIP_DIRS = ("\\program files\\windowsapps", "\\windows\\", "\\programdata\\microsoft",
                  "\\steamapps\\", "\\epic games\\", "\\riot games\\", "\\xboxgames\\", "\\ea games\\",
                  "\\ubisoft\\", "\\battle.net\\", "\\microsoft\\", "\\google\\chrome", "\\mozilla",
                  "\\nvidia", "\\amd\\", "\\intel\\", "\\jetbrains\\", "\\python", "\\node_modules\\",
                  "\\discord\\app-", "\\obs-studio\\", "\\common files\\")
_RISKY_DLL_KEYS = ("\\temp\\", "\\downloads\\", "\\desktop\\", "\\documents\\", "\\.minecraft\\",
                   "\\appdata\\roaming\\", "\\onedrive\\")
_HIDDEN_EXTS = (".exe", ".jar", ".dll", ".bat", ".ps1", ".vbs", ".ahk", ".cmd", ".scr")
_W_CUSTOM = []
_W_THROTTLE = None


class Throttle:
    """Limita o uso de CPU: trabalha `duty` do tempo e dorme o resto (nunca 100%)."""

    def __init__(self, duty=0.55, slice_s=0.035):
        self.duty = duty
        self.slice = slice_s
        self.t0 = time.perf_counter()

    def tick(self):
        el = time.perf_counter() - self.t0
        if el >= self.slice:
            time.sleep(el * (1.0 - self.duty) / self.duty)
            self.t0 = time.perf_counter()


def _lower_priority(idle=False):
    """Prioridade baixa de CPU e disco para o PC (e o jogo) não engasgarem."""
    try:
        p = psutil.Process()
        if os.name == "nt":
            p.nice(psutil.IDLE_PRIORITY_CLASS if idle else psutil.BELOW_NORMAL_PRIORITY_CLASS)
            try:
                p.ionice(psutil.IOPRIO_LOW)
            except Exception:
                pass
        else:
            p.nice(19 if idle else 10)
    except Exception:
        pass


def _pool_init(custom_strings):
    global _W_CUSTOM, _W_THROTTLE
    _W_CUSTOM = custom_strings or []
    _W_THROTTLE = Throttle(duty=0.5)
    _lower_priority(idle=True)


def _kind_cat(kind):
    return {"CHEAT": "Ameaças", "AUTOCLICKER": "Autoclickers", "BYPASS": "Bypass"}.get(kind, "Sistema")


def is_mc_path(lp):
    return any(k in lp for k in MC_PATH_KEYS)


def _skip_roots():
    roots = set()
    sysroot = os.environ.get("SystemRoot") or os.environ.get("windir")
    if sysroot:
        roots.add(os.path.normcase(sysroot))
    for pf in ("ProgramFiles", "ProgramFiles(x86)"):
        v = os.environ.get(pf)
        if v:
            roots.add(os.path.normcase(os.path.join(v, "WindowsApps")))
            roots.add(os.path.normcase(os.path.join(v, "Windows Defender")))
            roots.add(os.path.normcase(os.path.join(v, "Microsoft Office")))
    pd = os.environ.get("ProgramData")
    if pd:
        roots.add(os.path.normcase(os.path.join(pd, "Microsoft")))
        roots.add(os.path.normcase(os.path.join(pd, "Package Cache")))
    return roots


def fast_walk(top, visited, skip_dirs=SCAN_SKIP_DIRS, skip_roots=frozenset(), hidden_dirs=None, throttle=None):
    """os.scandir: tamanho, data e atributo 'oculto' vêm de graça (sem chamadas extras)."""
    stack = [top]
    while stack:
        d = stack.pop()
        key = os.path.normcase(d)
        if key in visited:
            continue
        visited.add(key)
        try:
            it = os.scandir(d)
        except OSError:
            continue
        files = []
        with it:
            for e in it:
                try:
                    if e.is_dir(follow_symlinks=False):
                        if e.name.lower() in skip_dirs:
                            continue
                        if os.path.normcase(e.path) in skip_roots:
                            continue
                        attrs = getattr(e.stat(follow_symlinks=False), "st_file_attributes", 0)
                        if attrs & _FILE_ATTRIBUTE_REPARSE:
                            continue
                        if hidden_dirs is not None and (attrs & _FILE_ATTRIBUTE_HIDDEN) and len(hidden_dirs) < 3000:
                            hidden_dirs.append(e.path)
                        stack.append(e.path)
                    elif e.is_file(follow_symlinks=False):
                        st = e.stat(follow_symlinks=False)
                        hidden = e.name.startswith(".") or bool(getattr(st, "st_file_attributes", 0) & _FILE_ATTRIBUTE_HIDDEN)
                        files.append((e.name, e.path, st.st_size, hidden, st.st_mtime))
                except OSError:
                    continue
                if throttle is not None:
                    throttle.tick()
        yield d, files


def _downgrade(sev):
    return {"CRITICAL": "HIGH", "HIGH": "MEDIUM"}.get(sev, sev)


def quick_file_checks(fname, full_path, hidden, mtime=0, logon=0):
    """Checagens baratas (só nome/atributo) — feitas direto no laço da varredura."""
    out = []
    fname_low = fname.lower()
    lp = full_path.lower()
    mc = is_mc_path(lp)
    if fname_low.endswith(".pf"):
        base = fname_low[:-3].rsplit("-", 1)[0]
        tag, inside = instance_tag(mtime, logon)
        for label, kind, sev, ev in detection_hits(base):
            out.append(("Suspeitos", {"name": f"Executado (Prefetch): {label}",
                                      "desc": "O Windows registrou a execução deste programa, mesmo que ele já tenha sido apagado. "
                                              + (tag or ""),
                                      "path": full_path, "severity": sev if inside else _downgrade(sev),
                                      "evidence": f"{fname} • {tag}" if tag else fname}))
        return out
    hits = detection_hits(fname)
    for label, kind, sev, ev in hits:
        cat = "Mods" if (mc and fname_low.endswith(".jar")) else _kind_cat(kind)
        out.append((cat, {"name": label, "desc": f"Arquivo com assinatura de {kind.lower()}.",
                          "path": full_path, "severity": sev, "evidence": ev}))
    if hidden and fname_low.endswith(_HIDDEN_EXTS):
        if hits:
            out.append(("Ocultos", {"name": f"Oculto [{hits[0][0]}]: {fname}", "desc": "Xit com atributo OCULTO — tentativa de esconder.",
                                    "path": full_path, "severity": "CRITICAL", "evidence": "attribute:hidden + assinatura"}))
        elif mc:
            out.append(("Ocultos", {"name": f"Arquivo oculto no Minecraft: {fname}", "desc": "Executável/jar oculto dentro da pasta do jogo/launcher.",
                                    "path": full_path, "severity": "HIGH", "evidence": "attribute:hidden"}))
        elif not fname_low.endswith(".dll") and any(k in lp for k in ("\\downloads\\", "\\desktop\\", "\\temp\\", "\\documents\\")):
            out.append(("Ocultos", {"name": f"Executável oculto: {fname}", "desc": "Executável com atributo oculto em pasta do usuário.",
                                    "path": full_path, "severity": "MEDIUM", "evidence": "attribute:hidden"}))
    return out


_SELF_PATHS = {os.path.normcase(os.path.abspath(p)) for p in (sys.argv[0] if sys.argv else "", __file__,
                                                                sys.executable if getattr(sys, "frozen", False) else "") if p}


def heavy_kind(fname_low, full_path, size):
    """Decide se o arquivo precisa de inspeção profunda — só onde faz sentido (economiza CPU)."""
    if size <= 0 or os.path.normcase(full_path) in _SELF_PATHS:
        return None
    lp = full_path.lower()
    if fname_low.endswith(".jar"):
        return "jar" if size < 80 * 1024 * 1024 else None
    if fname_low.endswith((".exe", ".scr")):
        if size < 25 * 1024 * 1024 and not any(sd in lp for sd in _EXE_SKIP_DIRS) and "\\program files" not in lp:
            return "exe"
        return None
    if fname_low.endswith(".dll"):
        if size < 20 * 1024 * 1024 and any(k in lp for k in _RISKY_DLL_KEYS) and not any(sd in lp for sd in _EXE_SKIP_DIRS):
            return "exe"
        return None
    if fname_low.endswith(ARCHIVE_EXTS):
        if ("\\resourcepacks\\" in lp or "\\texturepacks\\" in lp) and fname_low.endswith(".zip"):
            return "pack" if size < 300 * 1024 * 1024 else None
        if size < 150 * 1024 * 1024 and not any(sd in lp for sd in _EXE_SKIP_DIRS) and "\\program files" not in lp:
            return "archive"
        return None
    if fname_low == "pack.mcmeta" and ("\\resourcepacks\\" in lp or "\\texturepacks\\" in lp):
        return "packdir"
    if fname_low.endswith(SCRIPT_EXTS) and size < 1024 * 1024:
        if fname_low.endswith((".py", ".pyw")) and ("python" in lp or "\\lib\\" in lp or "\\program files" in lp):
            return None
        if any(sd in lp for sd in _EXE_SKIP_DIRS):
            return None
        return "script"
    if fname_low.endswith(TEXT_EXTS) and size < 3 * 1024 * 1024 and is_mc_path(lp):
        return "text"
    return None


def _pack_texture_transparent(read_png):
    """Xray pack: stone/deepslate/dirt quase transparentes."""
    see_through = []
    for tex in ("stone", "deepslate", "dirt", "netherrack", "andesite", "granite", "diorite", "tuff"):
        img = read_png(tex)
        if img is None:
            continue
        try:
            a = img.convert("RGBA").split()[3]
            hist = a.histogram()
            clear = sum(hist[:40]) / max(1, sum(hist))
            if clear >= 0.6:
                see_through.append(tex)
        except Exception:
            continue
    return see_through


def inspect_pack(path, is_dir=False):
    """Texture pack ilegal: nome/descrição (xray, anti-invis, overlay) + blocos transparentes."""
    evidences = []
    name = os.path.basename(path)
    n = norm(name)
    for w in ILLEGAL_PACK_WORDS:
        if _has_word_boundary(n, norm(w)):
            evidences.append(f"Nome do pack: '{w}'")
            break
    try:
        if is_dir:
            def read_bytes(rel):
                p = os.path.join(path, *rel.split("/"))
                if os.path.isfile(p) and os.path.getsize(p) < 4 * 1024 * 1024:
                    with open(p, "rb") as f:
                        return f.read()
                return None
        else:
            z = zipfile.ZipFile(path)
            names = set(z.namelist())

            def read_bytes(rel):
                if rel in names:
                    info = z.getinfo(rel)
                    if info.file_size < 4 * 1024 * 1024:
                        return z.read(rel)
                return None
        meta = read_bytes("pack.mcmeta")
        if meta:
            desc = meta.decode("utf-8", "ignore").lower()
            ndesc = norm(desc)
            for w in ILLEGAL_PACK_WORDS:
                if _has_word_boundary(ndesc, norm(w)):
                    evidences.append(f"Descrição do pack cita '{w}'")
                    break

        def read_png(tex):
            for folder in ("block", "blocks"):
                b = read_bytes(f"assets/minecraft/textures/{folder}/{tex}.png")
                if b:
                    try:
                        return Image.open(BytesIO(b))
                    except Exception:
                        return None
            return None
        clear = _pack_texture_transparent(read_png)
        if clear:
            evidences.append("Blocos transparentes (X-Ray): " + ", ".join(clear[:5]))
        if not is_dir:
            z.close()
    except Exception:
        pass
    if not evidences:
        return None, []
    sev = "CRITICAL" if any(e.startswith("Blocos") for e in evidences) else "HIGH"
    return sev, evidences


def heavy_inspect(kind, full_path, fname, custom_strings=None):
    """Inspeção profunda (roda nos processos auxiliares, em paralelo)."""
    cs = _W_CUSTOM if custom_strings is None else custom_strings
    out = []
    lp = full_path.lower()
    try:
        if kind == "jar":
            jsev, jev = deep_inspect_jar(full_path, custom_strings=cs)
            if jsev:
                cat = "Mods" if is_mc_path(lp) else "Ameaças"
                out.append((cat, {"name": f"{'Mod' if cat == 'Mods' else 'JAR'} com xit: {fname}",
                                  "desc": "Assinaturas de xit confirmadas DENTRO do jar (não só pelo nome).",
                                  "path": full_path, "severity": jsev, "evidence": " | ".join(jev[:4])}))
        elif kind == "exe":
            esev, eev = deep_inspect_exe(full_path)
            if esev:
                cat_e = "Autoclickers" if any("clic" in e.lower() or "cps" in e.lower() for e in eev) else "Ameaças"
                out.append((cat_e, {"name": f"Executável suspeito: {fname}", "desc": "Assinaturas binárias de xit/autoclicker/injetor.",
                                    "path": full_path, "severity": esev, "evidence": " | ".join(eev[:4])}))
        elif kind == "archive":
            asev, aev = inspect_archive(full_path, cs)
            if asev:
                out.append(("Ameaças", {"name": f"Compactado com xit: {fname}", "desc": "O arquivo .zip/.rar contém xit.",
                                        "path": full_path, "severity": asev, "evidence": " | ".join(aev[:4])}))
        elif kind in ("pack", "packdir"):
            target = full_path if kind == "pack" else os.path.dirname(full_path)
            psev, pev = inspect_pack(target, is_dir=(kind == "packdir"))
            if psev:
                out.append(("Mods", {"name": f"Texture pack ilegal: {os.path.basename(target)}",
                                     "desc": "Pack de vantagem (X-Ray / overlay / anti-invis).",
                                     "path": target, "severity": psev, "evidence": " | ".join(pev[:3])}))
        elif kind == "script":
            for lbl, sev, k in inspect_script(full_path):
                out.append((_kind_cat(k), {"name": f"Script: {lbl}", "desc": f"Encontrado no script {fname}.",
                                           "path": full_path, "severity": sev, "evidence": lbl}))
        elif kind == "text":
            txt_hits, strong = scan_text_file(full_path, custom_strings=cs)
            if txt_hits:
                sev = "HIGH" if strong else "LOW"
                if strong and any(k in txt_hits for k in TEXT_STRONG_HITS):
                    sev = "CRITICAL"
                out.append(("Textos", {"name": f"{'Rastro de xit' if strong else 'Menção'} em: {fname}",
                                       "desc": ("O xit deixou registro (carregou/ativou módulo)." if strong else
                                                "Só menção ao nome (fora do chat) — informativo.") +
                                               f" {len(txt_hits)} termo(s).",
                                       "path": full_path, "severity": sev, "evidence": ", ".join(txt_hits[:5])}))
    except Exception:
        pass
    return out


def heavy_batch(tasks):
    out = []
    for kind, full, fname in tasks:
        out.extend(heavy_inspect(kind, full, fname))
        if _W_THROTTLE is not None:
            _W_THROTTLE.tick()
    return out


def _scan_processes(log):
    processes = get_active_processes()
    log("Sistema", {"name": "Processos ativos", "desc": f"{len(processes)} processos varridos.", "severity": "LOW"})
    sysroot = os.path.normcase(os.environ.get("SystemRoot", "C:\\Windows")) + os.sep
    for pid, name, exe in processes:
        exe_l = os.path.normcase(exe or "")
        hits = scan_filename(name) + (scan_filename(os.path.basename(exe)) if exe else [])
        seen = set()
        for label, kind, sev, ev in hits:
            if label in seen:
                continue
            seen.add(label)
            if exe_l.startswith(sysroot) and kind != "CHEAT":
                continue
            log(_kind_cat(kind), {"name": label,
                                  "desc": f"Processo em execução AGORA (PID {pid}) — em instância." if kind != "INFO"
                                  else f"Ferramenta aberta (PID {pid}).",
                                  "path": exe or name, "severity": "CRITICAL" if kind == "CHEAT" else sev,
                                  "evidence": f"process:{name}"})
        # programa rodando a partir de Downloads/Desktop/Temp: confere o binário de verdade
        if exe and not hits and any(k in exe_l for k in ("\\downloads\\", "\\desktop\\", "\\temp\\", "\\documents\\")):
            esev, eev = deep_inspect_exe(exe)
            if esev:
                log("Autoclickers" if any("clic" in e.lower() or "cps" in e.lower() for e in eev) else "Ameaças",
                    {"name": f"Processo suspeito: {name}", "desc": f"Rodando agora (PID {pid}) com assinaturas de xit.",
                     "path": exe, "severity": esev, "evidence": " | ".join(eev[:4])})


def _scan_recycle(log, custom_strings):
    for original_name, full in scan_recycle_bin():
        base = os.path.basename((original_name or os.path.basename(full)).replace("\\", "/"))
        if not os.path.basename(full).startswith("$I"):
            continue
        rfile = os.path.join(os.path.dirname(full), "$R" + os.path.basename(full)[2:])
        fhits = detection_hits(base)
        for label, kind, sev, ev in fhits:
            log("Lixeira", {"name": f"Apagado: {label}",
                            "desc": f"Está na Lixeira — pode ter tentado esconder evidência.\nArquivo original: {original_name}",
                            "path": rfile if os.path.exists(rfile) else full, "severity": sev, "evidence": f"recyclebin:{base}"})
        if fhits:
            continue
        bl = base.lower()
        if bl.endswith(".jar") and os.path.isfile(rfile):
            jsev, jev = deep_inspect_jar(rfile, custom_strings)
            if jsev:
                log("Lixeira", {"name": f"Mod com xit apagado: {base}", "desc": f"Jar na Lixeira com xit dentro.\nOriginal: {original_name}",
                                "path": rfile, "severity": jsev, "evidence": " | ".join(jev[:3])})
        elif bl.endswith((".exe", ".dll")) and os.path.isfile(rfile):
            esev, eev = deep_inspect_exe(rfile)
            if esev:
                log("Lixeira", {"name": f"Executável com xit apagado: {base}", "desc": f"Original: {original_name}",
                                "path": rfile, "severity": esev, "evidence": " | ".join(eev[:3])})
        elif bl.endswith((".ahk", ".bat", ".ps1")) and os.path.isfile(rfile):
            for lbl, sev, k in inspect_script(rfile):
                log("Lixeira", {"name": f"Script apagado: {lbl}", "desc": f"Original: {original_name}",
                                "path": rfile, "severity": sev, "evidence": lbl})


def _scan_usb(log):
    current_usb = get_current_usb_devices()
    log("Sistema", {"name": f"USB conectados ({len(current_usb)})", "desc": "Dispositivos USB atualmente ligados.", "severity": "LOW"})
    for u in current_usb:
        cap, did = u.get("caption", "?"), u.get("device_id", "?")
        log("USB", {"name": f"USB: {cap}", "desc": f"Estado: {u.get('state', '?')}", "path": did,
                    "severity": "LOW", "status": "Ativo", "evidence": u.get("state", "")})
    seen_ids, shown = set(), 0
    for u in get_usb_history():
        did = u.get("device_id", "")
        if did in seen_ids:
            continue
        seen_ids.add(did)
        utype = u.get("type", "?")
        if utype in ("RecentDocs", "Atalho (.lnk)"):
            hits = detection_hits(os.path.basename(did.replace("\\", "/")))
            for label, kind, s, ev in hits:
                log("Suspeitos", {"name": f"Aberto recentemente: {label}", "desc": f"{utype} aponta para um xit — {u.get('state', '')}",
                                  "path": did, "severity": s, "evidence": utype})
            if hits:
                continue
        shown += 1
        if shown > 60:
            continue
        log("USB", {"name": f"{utype}: {u.get('caption', 'USB')[:60]}", "desc": f"{utype} — {u.get('state', '?')}",
                    "path": did, "severity": "LOW", "status": "Histórico", "evidence": utype})


def _scan_profiles(log, appdata):
    profiles_json = os.path.join(appdata, ".minecraft", "launcher_profiles.json")
    if not os.path.exists(profiles_json):
        return
    try:
        with open(profiles_json, "r", encoding="utf-8", errors="ignore") as f:
            data = json.load(f)
        for _pid, prof in (data.get("profiles") or {}).items():
            for check in (norm(prof.get("name", "")), norm(prof.get("lastVersionId", "")), norm(prof.get("javaArgs", ""))):
                for key, nkey, (label, sev) in _CHEAT_KEYS:
                    if len(nkey) >= 5 and nkey in check:
                        log("Suspeitos", {"name": f"Perfil do launcher com xit: {label}",
                                          "desc": f"Perfil '{prof.get('name', '?')}' → versão '{prof.get('lastVersionId', '?')}'.",
                                          "path": profiles_json, "severity": sev, "evidence": prof.get("name", "")})
            jargs = (prof.get("javaArgs") or "").lower()
            if "-javaagent:" in jargs and not any(k in jargs for k in LEGIT_AGENTS):
                log("Suspeitos", {"name": "Perfil com -javaagent desconhecido", "desc": "O perfil injeta um Java Agent no jogo.",
                                  "path": profiles_json, "severity": "HIGH", "evidence": jargs[:160]})
    except Exception:
        pass


def scan_worker(q, custom_strings):
    """Processo do scan: manda tudo para a interface pela fila `q`."""
    _lower_priority()
    throttle = Throttle(duty=0.55)

    def log(cat, item):
        q.put(("log", cat, item))

    def progress(p, text, stage=None):
        q.put(("progress", p, text, stage))

    try:
        progress(0.02, "Analisando processos em execução...", 0)
        logon = get_logon_time()
        if logon:
            log("Sistema", {"name": "Logon do usuário", "severity": "LOW",
                            "desc": "Tudo executado depois deste horário está EM INSTÂNCIA: "
                                    + datetime.fromtimestamp(logon).strftime("%d/%m/%Y %H:%M:%S")})
        try:
            _scan_processes(log)
        except Exception:
            pass

        progress(0.04, "Verificando Java Agents / injeção no Minecraft...", 1)
        try:
            for pid, agent, sev, ev in scan_running_java_agents():
                log("Ameaças", {"name": f"Java Agent no Minecraft (PID {pid})",
                                "desc": "O jogo foi aberto com -javaagent fora da lista de launchers legítimos.",
                                "path": agent, "severity": sev, "evidence": ev})
            for cat, item in scan_java_runtime():
                log(cat, item)
        except Exception:
            pass

        progress(0.05, "Coletando drives...", 2)
        if os.name == "nt":
            drives = [f"{chr(65 + i)}:\\" for i in range(26) if os.path.exists(f"{chr(65 + i)}:\\")]
        else:
            drives = ["/"]
        priority = get_priority_dirs()
        targets = priority + [d for d in drives if d not in priority]
        skip_roots = frozenset(_skip_roots())

        cpus = os.cpu_count() or 2
        workers = 1 if cpus <= 4 else 2
        pool = None
        try:
            pool = ProcessPoolExecutor(max_workers=workers, initializer=_pool_init, initargs=(custom_strings,))
        except Exception:
            pool = None
        pending = set()

        def collect(done):
            for f in done:
                try:
                    for cat, item in f.result():
                        log(cat, item)
                except Exception:
                    pass

        batch = []
        batch_bytes = 0

        def flush():
            nonlocal batch, batch_bytes, pool, pending
            if not batch:
                return
            tasks, batch, batch_bytes = batch, [], 0
            if pool is not None:
                try:
                    pending.add(pool.submit(heavy_batch, tasks))
                    if len(pending) > workers * 3:
                        done, pending = wait(pending, return_when=FIRST_COMPLETED)
                        collect(done)
                    return
                except Exception:
                    pool = None
            for kind, full, fname in tasks:
                for cat, item in heavy_inspect(kind, full, fname, custom_strings):
                    log(cat, item)
                throttle.tick()

        files_seen = 0
        visited = set()
        hidden_dirs = []
        last_ui = 0.0
        stop = False
        for target in targets:
            if stop or not os.path.exists(target):
                continue
            for root, files in fast_walk(target, visited, skip_roots=skip_roots, hidden_dirs=hidden_dirs, throttle=throttle):
                for fname, full, size, hidden, mtime in files:
                    files_seen += 1
                    fl = fname.lower()
                    if _has_relevant_ext(fl) or fl.endswith(TEXT_EXTS) or fl == "pack.mcmeta":
                        for cat, item in quick_file_checks(fname, full, hidden, mtime, logon):
                            log(cat, item)
                        kind = heavy_kind(fl, full, size)
                        if kind:
                            batch.append((kind, full, fname))
                            batch_bytes += size
                            if len(batch) >= 48 or batch_bytes > 16 * 1024 * 1024:
                                flush()
                    if files_seen >= MAX_FILES:
                        stop = True
                        break
                now = time.time()
                if now - last_ui > 0.3:
                    last_ui = now
                    if pending:
                        done = {f for f in pending if f.done()}
                        pending -= done
                        collect(done)
                    prog = 0.05 + min(files_seen / TOTAL_EST, 1.0) * 0.80
                    short = os.path.basename(root) or root
                    q.put(("files", files_seen))
                    progress(prog, f"Verificando: {short[:38]}")
                if stop:
                    break
        flush()
        if pending:
            progress(0.86, "Concluindo análises profundas...")
            done, _ = wait(pending)
            collect(done)
        if pool is not None:
            pool.shutdown(wait=True)
        q.put(("files", files_seen))

        progress(0.88, "Conferindo mods desativados dos launchers...", 3)
        try:
            for mdir in get_mod_dirs():
                for root, files in fast_walk(mdir, set(), throttle=throttle):
                    for fname, full, size, hidden, mtime in files:
                        if fname.lower().endswith((".jar.disabled", ".jar.old", ".jar.bak")):
                            jsev, jev = deep_inspect_jar(full, custom_strings)
                            if jsev:
                                log("Mods", {"name": f"Mod com xit desativado: {fname}", "desc": "Mod renomeado para não carregar (tentativa de esconder).",
                                             "path": full, "severity": jsev, "evidence": " | ".join(jev[:3])})
        except Exception:
            pass

        progress(0.92, "Analisando perfis do launcher...", 4)
        appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
        _scan_profiles(log, appdata)

        progress(0.93, "Verificando dispositivos USB...", 5)
        try:
            _scan_usb(log)
        except Exception:
            pass

        progress(0.95, "Varrendo Lixeira do Windows...", 6)
        try:
            _scan_recycle(log, custom_strings)
        except Exception:
            pass

        progress(0.97, "Conferindo pastas ocultas...", 7)
        for path_h in hidden_dirs:
            for label, _, sev, ev in detection_hits(os.path.basename(path_h)):
                log("Ocultos", {"name": f"Pasta oculta: {label}", "desc": "Pasta OCULTA com nome de xit.",
                                "path": path_h, "severity": sev, "evidence": "hidden folder"})

        progress(0.98, "Finalizando relatório...", 8)
        q.put(("done",))
    except Exception as e:
        q.put(("error", str(e)))

# ==============================================================================
#                      ÍCONES, FONTES E UTILITÁRIOS DE IMAGEM
# ==============================================================================

F_HEAD = "Bahnschrift SemiBold"
F_HEAD_LIGHT = "Bahnschrift Light"
F_BODY = "Segoe UI"
F_SEMI = "Segoe UI Semibold"
F_MONO = "Consolas"
F_ICON = "Segoe MDL2 Assets"
F_SYMBOL = "Segoe UI Symbol"

# Glifos da fonte "Segoe MDL2 Assets" (Windows 10/11) — ícones de linha fina
ICONS = {
    "home": "\uE80F", "gear": "\uE713", "search": "\uE721", "warn": "\uE7BA", "check": "\uE73E",
    "cancel": "\uE711", "folder": "\uE8B7", "folder_open": "\uE838", "doc": "\uE8A5", "usb": "\uE88E",
    "globe": "\uE774", "refresh": "\uE72C", "play": "\uE768", "copy": "\uE8C8", "delete": "\uE74D",
    "download": "\uE896", "upload": "\uE898", "info": "\uE946", "clock": "\uE823", "stopwatch": "\uE916",
    "shield": "\uEA18", "admin": "\uE7EF", "chat": "\uE8BD", "monitor": "\uE7F4", "library": "\uE8F1",
    "list": "\uE8FD", "code": "\uE943", "eye": "\uE7B3", "game": "\uE7FC", "open": "\uE8E5",
    "tag": "\uE8EC", "chevron": "\uE76C", "people": "\uE716", "target": "\uE7C1", "help": "\uE897",
}
# Substitutos simples caso a fonte de ícones não exista (Linux / Windows antigo)
ICONS_FALLBACK = {
    "home": "⌂", "gear": "⚙", "search": "⌕", "warn": "⚠", "check": "✓", "cancel": "✕",
    "folder": "▣", "folder_open": "▤", "doc": "▤", "usb": "⏚", "globe": "◍", "refresh": "↻",
    "play": "▶", "copy": "⧉", "delete": "✖", "download": "↓", "upload": "↑", "info": "ⓘ",
    "clock": "◷", "stopwatch": "◷", "shield": "⛨", "admin": "⚿", "chat": "✉", "monitor": "▭",
    "library": "▥", "list": "≡", "code": "⌘", "eye": "◉", "game": "✥", "open": "↗",
    "tag": "⌗", "chevron": "›", "people": "☺", "target": "⊕", "help": "?",
}
SPINNER = ["◐", "◓", "◑", "◒"]

SEV_COLORS = {"CRITICAL": SEV_CRITICAL, "HIGH": SEV_HIGH, "MEDIUM": SEV_MEDIUM, "LOW": SEV_LOW}
SEV_LABELS = {"CRITICAL": "Crítico", "HIGH": "Alto", "MEDIUM": "Médio", "LOW": "Baixo"}
SEV_TINTS = {"CRITICAL": (RED_BG, RED_BD), "HIGH": ("#1E1E1E", "#8A8A8A"),
             "MEDIUM": (AMBER_BG, AMBER_BD), "LOW": (BLUE_BG, BLUE_BD)}
SEV_RANK = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}

LOG_CATEGORIES = ["Ameaças", "Autoclickers", "Bypass", "Mods", "Ocultos",
                  "Textos", "Lixeira", "USB", "Suspeitos", "Sistema"]
DETECTION_CATEGORIES = ["Ameaças", "Autoclickers", "Bypass", "Mods", "Ocultos",
                        "Textos", "Lixeira", "Suspeitos"]
CATEGORY_INFO = {
    "Ameaças": ("warn", "Ameaças", "Clientes de xit, JARs e EXEs com assinatura de trapaça."),
    "Autoclickers": ("game", "Autoclickers", "Autoclickers, macros e scripts AutoHotkey."),
    "Bypass": ("shield", "Bypass e Injetores", "Limpadores de vestígios, injetores e burla de screenshare."),
    "Mods": ("library", "Mods dos Launchers", "Mods suspeitos nas pastas dos launchers."),
    "Ocultos": ("eye", "Arquivos Ocultos", "Arquivos e pastas com atributo oculto."),
    "Textos": ("doc", "Textos e Logs", "Menções a xit em logs, configs e arquivos de texto."),
    "Lixeira": ("delete", "Lixeira", "Arquivos de xit apagados que ainda estão na Lixeira."),
    "USB": ("usb", "Dispositivos USB", "USB conectados agora e histórico de dispositivos."),
    "Suspeitos": ("search", "Vestígios", "Rastros no Prefetch e perfis suspeitos do launcher."),
    "Sistema": ("monitor", "Sistema", "Informações gerais coletadas durante a verificação."),
}
SCAN_STAGES = ["Processos", "Minecraft em execução", "Arquivos e drives", "Mods dos launchers",
               "Perfis do launcher", "Dispositivos USB", "Lixeira", "Arquivos ocultos",
               "Relatório"]


def _img_from_b64(b64, mode="RGBA"):
    try:
        return Image.open(BytesIO(base64.b64decode(b64))).convert(mode)
    except Exception:
        img = Image.new(mode, (256, 256), (5, 5, 5) if mode == "RGB" else (0, 0, 0, 0))
        if mode == "RGBA":
            ImageDraw.Draw(img).ellipse((32, 32, 224, 224), outline=BLUE_NEON, width=14)
        return img


def mono_photo(img, brightness=0.6):
    g = ImageOps.autocontrast(ImageOps.grayscale(img), cutoff=1)
    return ImageEnhance.Brightness(g).enhance(brightness).convert("RGB")


def mono_logo(img):
    r, g, b, a = img.convert("RGBA").split()
    lum = ImageEnhance.Brightness(ImageOps.grayscale(Image.merge("RGB", (r, g, b)))).enhance(1.6)
    return Image.merge("RGBA", (lum, lum, lum, a))


def _hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def cover_image(src, w, h, anchor=(0.5, 0.5)):
    """Redimensiona cobrindo a área (como CSS background-size: cover)."""
    sw, sh = src.size
    scale = max(w / sw, h / sh)
    nw, nh = max(1, int(sw * scale + 0.5)), max(1, int(sh * scale + 0.5))
    img = src.resize((nw, nh), Image.BILINEAR)
    x = int((nw - w) * anchor[0])
    y = int((nh - h) * anchor[1])
    return img.crop((x, y, x + w, y + h))


def shade_horizontal(img, color=BG_DEEP, start=0.92, end=0.0, stop=0.62):
    """Escurece a esquerda (para texto legível) com um degradê horizontal."""
    w, h = img.size
    r, g, b = _hex_rgb(color)
    grad = Image.new("L", (256, 1))
    for i in range(256):
        t = i / 255
        a = start + (end - start) * min(1.0, t / max(stop, 0.01))
        grad.putpixel((i, 0), int(max(0, min(1, a)) * 255))
    mask = grad.resize((w, h), Image.BILINEAR)
    over = Image.new("RGBA", (w, h), (r, g, b, 255))
    base = img.convert("RGBA")
    base.paste(over, (0, 0), mask)
    return base


def shade_bottom(img, color=BG_DEEP, strength=0.85, height=0.45):
    w, h = img.size
    r, g, b = _hex_rgb(color)
    grad = Image.new("L", (1, 256))
    for i in range(256):
        t = i / 255
        a = 0 if t < 1 - height else (t - (1 - height)) / height * strength
        grad.putpixel((0, i), int(a * 255))
    mask = grad.resize((w, h), Image.BILINEAR)
    base = img.convert("RGBA")
    base.paste(Image.new("RGBA", (w, h), (r, g, b, 255)), (0, 0), mask)
    return base


def glass_panel(img, box, radius, fill=(30, 30, 30, 70), outline=(230, 230, 230, 170),
                width=2, glow=None):
    """Desenha um painel de vidro translúcido (com brilho opcional) sobre a imagem."""
    base = img.convert("RGBA")
    if glow:
        g = Image.new("RGBA", base.size, (0, 0, 0, 0))
        pad = 6
        ImageDraw.Draw(g).rounded_rectangle((box[0] - pad, box[1] - pad, box[2] + pad, box[3] + pad),
                                            radius + pad, fill=glow)
        base = Image.alpha_composite(base, g.filter(ImageFilter.GaussianBlur(18)))
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).rounded_rectangle(box, radius, fill=fill, outline=outline, width=width)
    return Image.alpha_composite(base, layer)


def paste_center(img, overlay, cx, cy):
    base = img.convert("RGBA")
    base.alpha_composite(overlay, (int(cx - overlay.width / 2), int(cy - overlay.height / 2)))
    return base


def spaced(text, n=1):
    return (" " * n).join(text)


def round_rect_points(x1, y1, x2, y2, r):
    return [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
            x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]


class BgCanvas(tk.Canvas):
    """Canvas com imagem de fundo responsiva (cover) + camadas desenhadas em PIL."""

    def __init__(self, master, source, anchor=(0.5, 0.5), overlay=None, layout=None,
                 bg=BG_DEEP, **kw):
        super().__init__(master, highlightthickness=0, bd=0, bg=bg, **kw)
        self.source = source
        self.anchor = anchor
        self.overlay = overlay
        self.layout = layout
        self._photo = None
        self._job = None
        self._size = (0, 0)
        self.bind("<Configure>", self._on_configure, add="+")

    def _on_configure(self, e):
        if (e.width, e.height) == self._size:
            return
        self._size = (e.width, e.height)
        if self._job:
            self.after_cancel(self._job)
        self._job = self.after(50, self.refresh)

    def refresh(self):
        self._job = None
        w, h = self.winfo_width(), self.winfo_height()
        if w < 8 or h < 8:
            return
        try:
            img = cover_image(self.source, w, h, self.anchor)
            if self.overlay:
                img = self.overlay(img, w, h) or img
            self._photo = ImageTk.PhotoImage(img.convert("RGB"), master=self)
            self.delete("all")
            self.create_image(0, 0, image=self._photo, anchor="nw", tags="bg")
            if self.layout:
                self.layout(self, w, h)
        except Exception:
            pass


class Tooltip:
    def __init__(self, widget, text):
        self.widget, self.text, self.tip, self.job = widget, text, None, None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")

    def _schedule(self, _e=None):
        self.job = self.widget.after(350, self._show)

    def _show(self):
        try:
            x = self.widget.winfo_rootx() + 10
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
            self.tip = tk.Toplevel(self.widget)
            self.tip.wm_overrideredirect(True)
            self.tip.wm_geometry(f"+{x}+{y}")
            tk.Label(self.tip, text=self.text, bg=BG_CARD_HOVER, fg=TEXT_MAIN, font=(F_BODY, 9),
                     padx=10, pady=6, wraplength=260, justify="left",
                     highlightthickness=1, highlightbackground=BORDER_GLOW).pack()
        except Exception:
            self.tip = None

    def _hide(self, _e=None):
        if self.job:
            try:
                self.widget.after_cancel(self.job)
            except Exception:
                pass
            self.job = None
        if self.tip:
            try:
                self.tip.destroy()
            except Exception:
                pass
            self.tip = None


class GlowButton(ctk.CTkButton):
    """Botão principal com borda que pulsa suavemente."""
    _GLOW_COLS = ["#5C5C5C", "#7A7A7A", "#9A9A9A", "#BDBDBD", "#FFFFFF", "#BDBDBD", "#9A9A9A", "#7A7A7A"]

    def __init__(self, master, glow=False, **kwargs):
        kwargs.pop("data_safe", None)
        kwargs.setdefault("fg_color", "#F2F2F2")
        kwargs.setdefault("hover_color", "#D6D6D6")
        kwargs.setdefault("text_color", TEXT_ON_LIGHT)
        kwargs.setdefault("text_color_disabled", "#5C5C5C")
        kwargs.setdefault("corner_radius", 10)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", BLUE_NEON)
        kwargs.setdefault("font", (F_HEAD, 14))
        super().__init__(master, **kwargs)
        self._glow_t = 0
        self._hovering = False
        self.bind("<Enter>", self._g_enter, add="+")
        self.bind("<Leave>", self._g_leave, add="+")
        if glow:
            self.after(120, self._animate_glow)

    def _animate_glow(self):
        try:
            if not self.winfo_exists():
                return
            if not self._hovering and self.winfo_ismapped():
                self._glow_t = (self._glow_t + 1) % len(self._GLOW_COLS)
                self.configure(border_color=self._GLOW_COLS[self._glow_t])
            self.after(420, self._animate_glow)
        except Exception:
            pass

    def _g_enter(self, _e=None):
        self._hovering = True
        try:
            self.configure(border_color=BLUE_GLOW)
        except Exception:
            pass

    def _g_leave(self, _e=None):
        self._hovering = False


# ==============================================================================
#                            INTERFACE GRÁFICA
# ==============================================================================

class CelestialScanner(ctk.CTk):
    def __init__(self):
        ctk.set_appearance_mode("dark")
        super().__init__()
        self.title(f"{APP_NAME} {VERSION} — Anti-Cheat System")
        self.geometry("1320x840")
        self.minsize(1200, 780)
        self.configure(fg_color=BG_DEEP)

        self.scanning = False
        self.scan_start = 0
        self.scan_end = 0
        self.logs_data = self._empty_logs()
        self._log_keys = set()
        self._flagged_paths = set()
        self._lock = threading.Lock()
        self._ui_q = queue.Queue()
        self._recent = deque(maxlen=5)
        self.total_detections = 0
        self.total_files = 0
        self._progress = 0.0
        self._progress_shown = 0.0
        self._status_text = "Pronto para iniciar a verificação."
        self._stage = -1
        self._scan_finished = False
        self._crit_found = False
        self._last_recent_sig = None
        self._spin = 0
        self.current_category = "Ameaças"
        self._log_items = []
        self._log_rendered = 0
        self.is_admin = is_admin()
        self.custom_strings = load_custom_strings()
        self.scale = 1.0
        self._active_view = "dash"
        self._scan_q = None
        self._scan_proc = None
        self._last_beep = 0
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._icon_font_ok = True
        try:
            self._icon_font_ok = F_ICON in set(tkfont.families(self))
        except Exception:
            self._icon_font_ok = False

        self.load_assets()
        self.build_splash()
        self.build_main()
        self.show_splash()
        self._pump_ui()
        self._ui_tick()
        self.tick_stats()

    # ------------------- THREAD-SAFE UI ---------------------------------------
    def ui(self, fn):
        """Agenda uma função para rodar na thread da interface (seguro p/ threads)."""
        self._ui_q.put(fn)

    def _pump_ui(self):
        try:
            for _ in range(200):
                fn = self._ui_q.get_nowait()
                try:
                    fn()
                except Exception:
                    pass
        except queue.Empty:
            pass
        self.after(40, self._pump_ui)

    def S(self, v):
        return int(v * self.scale)

    def ic(self, key):
        return (ICONS if self._icon_font_ok else ICONS_FALLBACK).get(key, "•")

    def icon_font(self, size):
        return (F_ICON, size) if self._icon_font_ok else (F_SYMBOL, size)

    def _empty_logs(self):
        return {c: [] for c in LOG_CATEGORIES}

    # ------------------- ASSETS -------------------------------------------------
    def load_assets(self):
        try:
            self.scale = ctk.ScalingTracker.get_widget_scaling(self)
        except Exception:
            self.scale = 1.0
        self.raw_logo = mono_logo(_img_from_b64(LOGO_B64))
        self.ocean_img = mono_photo(_img_from_b64(OCEAN_B64, "RGB"), 0.55)
        self.whale_img = mono_photo(_img_from_b64(WHALE_B64, "RGB"), 0.6)
        self.logo_side = ctk.CTkImage(self.raw_logo, size=(78, 78))
        self.logo_small = ctk.CTkImage(self.raw_logo, size=(34, 34))
        self._ico_path = None
        try:
            if os.name == "nt":
                self._ico_path = os.path.join(os.environ.get("TEMP", "."), "celestial_scan_icon.ico")
                self.raw_logo.save(self._ico_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128)])
        except Exception:
            self._ico_path = None
        try:
            self._icon_photo = ImageTk.PhotoImage(self.raw_logo.resize((64, 64), Image.LANCZOS), master=self)
            self.iconphoto(True, self._icon_photo)
        except Exception:
            pass
        self.after(260, lambda: self._apply_icon(self))

    def _apply_icon(self, win):
        try:
            if self._ico_path:
                win.iconbitmap(self._ico_path)
            elif getattr(self, "_icon_photo", None):
                win.iconphoto(False, self._icon_photo)
        except Exception:
            pass

    # ------------------- SPLASH (tela de entrada) -----------------------------
    def build_splash(self):
        self._splash_btn_box = (0, 0, 0, 0)
        self._splash_hover = False
        self._splash_glow_t = 0
        self.splash = BgCanvas(self, self.ocean_img, anchor=(0.5, 0.35),
                               overlay=self._splash_overlay, layout=self._splash_layout)
        self.splash.bind("<Motion>", self._splash_motion, add="+")
        self.splash.bind("<Button-1>", self._splash_click, add="+")

    def _splash_geom(self, w, h):
        logo = int(min(h * 0.30, 280))
        logo_cy = int(h * 0.26)
        title_y = logo_cy + logo // 2 + int(h * 0.06)
        bw, bh = self.S(480), self.S(66)
        by = title_y + self.S(118)
        return logo, logo_cy, title_y, (w // 2 - bw // 2, by, w // 2 + bw // 2, by + bh)

    def _splash_overlay(self, img, w, h):
        img = shade_bottom(img, strength=0.55, height=0.35)
        logo, logo_cy, title_y, btn = self._splash_geom(w, h)
        glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
        r = int(logo * 0.62)
        ImageDraw.Draw(glow).ellipse((w // 2 - r, logo_cy - r, w // 2 + r, logo_cy + r), fill=(255, 255, 255, 34))
        img = Image.alpha_composite(img, glow.filter(ImageFilter.GaussianBlur(40)))
        img = paste_center(img, self.raw_logo.resize((logo, logo), Image.LANCZOS), w // 2, logo_cy)
        small = self.raw_logo.resize((self.S(40), self.S(40)), Image.LANCZOS)
        img.alpha_composite(small, (self.S(26), self.S(18)))
        img = glass_panel(img, btn, self.S(12), fill=(242, 242, 242, 255), outline=(255, 255, 255, 0),
                          width=1, glow=(255, 255, 255, 70))
        return img

    def _splash_layout(self, c, w, h):
        logo, logo_cy, title_y, btn = self._splash_geom(w, h)
        self._splash_btn_box = btn
        s = self.S
        # topo esquerdo
        c.create_text(s(78), s(30), text="CELESTIAL", anchor="w", fill=TEXT_MAIN, font=(F_HEAD, -s(17)))
        f = tkfont.Font(family=F_HEAD, size=-s(17))
        c.create_text(s(78) + f.measure("CELESTIAL "), s(30), text="SCAN", anchor="w", fill=BLUE_NEON, font=(F_HEAD, -s(17)))
        c.create_text(s(79), s(50), text=spaced("ANTI-CHEAT SYSTEM"), anchor="w", fill=TEXT_MUTED, font=(F_BODY, -s(10)))
        # textos laterais
        c.create_text(s(30), int(h * 0.30), text="DETECTA\nPROTEGE\nPRESERVA\nO JOGO REAL", anchor="nw",
                      fill=TEXT_MUTED, font=(F_BODY, -s(12)))
        c.create_line(s(30), int(h * 0.30) + s(84), s(48), int(h * 0.30) + s(84), fill=BLUE_NEON, width=2)
        c.create_text(w - s(30), s(70), text="JOGO\nLIMPO\nSEMPRE\nMAIS LONGE", anchor="ne", justify="left",
                      fill=TEXT_MUTED, font=(F_BODY, -s(12)))
        c.create_line(w - s(48), s(158), w - s(30), s(158), fill=BLUE_NEON, width=2)
        # título central
        tf = tkfont.Font(family=F_HEAD, size=-s(58))
        tw1, tw2 = tf.measure("CELESTIAL "), tf.measure("SCAN")
        x0 = w // 2 - (tw1 + tw2) // 2
        c.create_text(x0, title_y, text="CELESTIAL", anchor="w", fill="#FFFFFF", font=tf)
        c.create_text(x0 + tw1, title_y, text="SCAN", anchor="w", fill=BLUE_NEON, font=tf)
        c.create_text(w // 2, title_y + s(50), text=spaced("ANTI-CHEAT SYSTEM", 2), fill=TEXT_MUTED,
                      font=(F_BODY, -s(15)))
        # botão INICIAR SCAN
        x1, y1, x2, y2 = btn
        c.create_polygon(round_rect_points(x1, y1, x2, y2, s(12)), smooth=True, fill="",
                         outline=BLUE_NEON, width=2, tags="btn_outline")
        bf = tkfont.Font(family=F_HEAD, size=-s(22))
        label = spaced("INICIAR SCAN", 1)
        lw = bf.measure(label)
        ix = w // 2 - lw // 2 - s(18)
        c.create_text(ix, (y1 + y2) // 2, text=self.ic("play"), fill=TEXT_ON_LIGHT, font=self.icon_font(-s(20)))
        c.create_text(ix + s(26), (y1 + y2) // 2, text=label, anchor="w", fill=TEXT_ON_LIGHT, font=bf, tags="btn_text")
        c.create_text(w // 2, y2 + s(26), text="A verificação apenas lê e reporta — nunca apaga nada do jogador.",
                      fill=TEXT_DIM, font=(F_BODY, -s(11)))
        # recursos
        feats = [("shield", "AMBIENTE\nSEGURO"), ("target", "DETECÇÃO\nAVANÇADA"),
                 ("check", "JOGO\nJUSTO"), ("people", "COMUNIDADE\nMAIS FORTE")]
        fy = min(h - s(150), y2 + s(84))
        gap = s(170)
        start = w // 2 - gap * 3 // 2
        for i, (ico, txt) in enumerate(feats):
            fx = start + i * gap
            c.create_text(fx, fy, text=self.ic(ico), fill=BLUE_BRIGHT, font=self.icon_font(-s(24)))
            c.create_text(fx, fy + s(36), text=txt, fill=TEXT_MUTED, justify="center", font=(F_BODY, -s(10)))
            if i:
                c.create_line(fx - gap // 2, fy - s(14), fx - gap // 2, fy + s(48), fill=BORDER_STRONG)
        # links
        ly = h - s(30)
        links = [("chat", "Suporte"), ("chat", "Discord")]
        lx = w // 2 - s(70)
        for i, (ico, txt) in enumerate(links):
            x = lx + i * s(140)
            t1 = c.create_text(x - s(12), ly, text=self.ic(ico), fill=BLUE_BRIGHT, font=self.icon_font(-s(14)), tags=("link",))
            t2 = c.create_text(x + s(2), ly, text=txt, anchor="w", fill=TEXT_MAIN, font=(F_BODY, -s(13)), tags=("link",))
            for t in (t1, t2):
                c.tag_bind(t, "<Button-1>", lambda e: webbrowser.open(DISCORD_LINK))
                c.tag_bind(t, "<Enter>", lambda e: c.configure(cursor="hand2"))
                c.tag_bind(t, "<Leave>", lambda e: c.configure(cursor=""))
            if i:
                c.create_line(x - s(44), ly - s(9), x - s(44), ly + s(9), fill=BORDER_STRONG)
        c.create_text(s(26), h - s(22), text=VERSION, anchor="w", fill=TEXT_DIM, font=(F_BODY, -s(11)))
        c.create_text(w - s(30), h - s(66), text="CELESTIAL SCAN", anchor="e", fill=TEXT_MAIN, font=(F_HEAD, -s(15)))
        c.create_text(w - s(30), h - s(42), text="A CLEANER TOMORROW\nFOR FAIR PLAY", anchor="e", justify="left",
                      fill=TEXT_MUTED, font=(F_BODY, -s(10)))
        self._splash_paint_btn()

    def _splash_in_btn(self, x, y):
        x1, y1, x2, y2 = self._splash_btn_box
        return x1 <= x <= x2 and y1 <= y <= y2

    def _splash_motion(self, e):
        hov = self._splash_in_btn(e.x, e.y)
        if hov != self._splash_hover:
            self._splash_hover = hov
            self.splash.configure(cursor="hand2" if hov else "")
            self._splash_paint_btn()

    def _splash_paint_btn(self):
        cols = ["#8A8A8A", "#BDBDBD", "#FFFFFF", "#BDBDBD"]
        col = "#FFFFFF" if self._splash_hover else cols[self._splash_glow_t % len(cols)]
        try:
            self.splash.itemconfigure("btn_outline", outline=col, width=3 if self._splash_hover else 2)
            self.splash.itemconfigure("btn_text", fill="#000000" if self._splash_hover else TEXT_ON_LIGHT)
        except Exception:
            pass

    def _splash_pulse(self):
        if not self.splash.winfo_ismapped():
            return
        self._splash_glow_t += 1
        self._splash_paint_btn()
        self.after(380, self._splash_pulse)

    def _splash_click(self, e):
        if self._splash_in_btn(e.x, e.y):
            self.enter_panel(start=True)

    def show_splash(self):
        self.main.pack_forget()
        self.splash.pack(fill="both", expand=True)
        self.after(200, self._splash_pulse)

    def enter_panel(self, start=False):
        self.splash.pack_forget()
        self.main.pack(fill="both", expand=True)
        self.show_view("dash")
        if start:
            self.after(250, self.start_scan)

    # ------------------- ESTRUTURA PRINCIPAL ----------------------------------
    def build_main(self):
        self.main = ctk.CTkFrame(self, fg_color=BG_DEEP, corner_radius=0)
        self.sidebar = ctk.CTkFrame(self.main, fg_color=BG_PANEL, width=252, corner_radius=0,
                                    border_width=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        ctk.CTkFrame(self.main, fg_color=BORDER_SOFT, width=1, corner_radius=0).pack(side="left", fill="y")
        self.build_sidebar()

        right = ctk.CTkFrame(self.main, fg_color=BG_DEEP, corner_radius=0)
        right.pack(side="left", fill="both", expand=True)
        self.build_statusbar(right)
        self.stage = ctk.CTkFrame(right, fg_color=BG_DEEP, corner_radius=0)
        self.stage.pack(side="top", fill="both", expand=True)

        self.build_dashboard()
        self.build_result()
        self.build_logs()
        self.build_extractor()
        self.build_strings()
        self.build_presence()
        self.build_settings()
        self._views = {"dash": self.dash, "result": self.result_view, "logs": self.logs_view,
                       "extractor": self.extractor_view, "strings": self.strings_view,
                       "presence": self.presence_view, "settings": self.settings_view}

    # ------------------- SIDEBAR -----------------------------------------------
    def build_sidebar(self):
        head = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        head.pack(fill="x", padx=18, pady=(26, 18))
        logo = ctk.CTkLabel(head, image=self.logo_side, text="", cursor="hand2")
        logo.pack()
        logo.bind("<Button-1>", lambda e: self.show_splash(), add="+")
        Tooltip(logo, "Voltar para a tela de entrada")
        name = ctk.CTkFrame(head, fg_color="transparent")
        name.pack(pady=(8, 0))
        ctk.CTkLabel(name, text="CELESTIAL ", font=(F_HEAD, 22), text_color=TEXT_MAIN).pack(side="left")
        ctk.CTkLabel(name, text="SCAN", font=(F_HEAD, 22), text_color=BLUE_NEON).pack(side="left")
        ctk.CTkLabel(head, text="ANTI-CHEAT SCREENSHARE SCANNER", font=(F_BODY, 9),
                     text_color=TEXT_MUTED).pack()

        self.nav_items = {}
        for key, label, icon in [("dash", "Dashboard", "home"), ("result", "Resultado", "shield"),
                                 ("logs", "Logs", "list"), ("extractor", "String Extractor", "code"),
                                 ("strings", "Strings Custom", "tag"), ("presence", "Presença", "eye"),
                                 ("settings", "Ajustes", "gear")]:
            self.nav_items[key] = self.make_nav_item(self.sidebar, icon, label,
                                                     lambda k=key: self.show_view(k))

        ctk.CTkLabel(self.sidebar, text="SUPORTE", font=(F_SEMI, 11), text_color=TEXT_MUTED).pack(
            anchor="w", padx=30, pady=(18, 4))
        ctk.CTkFrame(self.sidebar, fg_color=BORDER_SOFT, height=1).pack(fill="x", padx=26, pady=(0, 6))
        self.make_nav_item(self.sidebar, "chat", "Discord", lambda: webbrowser.open(DISCORD_LINK))

        card = ctk.CTkFrame(self.sidebar, fg_color=BG_CARD, corner_radius=12, border_width=1,
                            border_color=BORDER_SOFT)
        card.pack(side="bottom", fill="x", padx=16, pady=18)
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=10)
        ctk.CTkLabel(inner, image=self.logo_small, text="").pack(side="left")
        box = ctk.CTkFrame(inner, fg_color="transparent")
        box.pack(side="left", padx=10)
        ctk.CTkLabel(box, text=_safe_user()[:22], font=(F_SEMI, 12), text_color=TEXT_MAIN, height=18).pack(anchor="w")
        adm = "Administrador" if self.is_admin else "Sem administrador"
        ctk.CTkLabel(box, text=f"{adm} • {VERSION}", font=(F_BODY, 10),
                     text_color=SEV_OK if self.is_admin else SEV_HIGH, height=16).pack(anchor="w")

    def make_nav_item(self, parent, icon, label, command):
        item = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=10, height=44,
                            border_width=1, border_color=BG_PANEL, cursor="hand2")
        item.pack(fill="x", padx=14, pady=2)
        item.pack_propagate(False)
        bar = ctk.CTkFrame(item, fg_color=BG_PANEL, width=3, corner_radius=2)
        bar.pack(side="left", fill="y", padx=(4, 0), pady=9)
        ic = ctk.CTkLabel(item, text=self.ic(icon), font=self.icon_font(17), text_color=TEXT_MUTED,
                          width=34, cursor="hand2")
        ic.pack(side="left", padx=(10, 6))
        tx = ctk.CTkLabel(item, text=label, font=(F_BODY, 14), text_color=TEXT_MUTED, anchor="w", cursor="hand2")
        tx.pack(side="left", fill="x", expand=True)
        item._parts = (bar, ic, tx)
        item._active = False

        def enter(_e=None):
            if not item._active:
                item.configure(fg_color=BG_CARD)

        def leave(_e=None):
            if not item._active:
                item.configure(fg_color="transparent")

        for w in (item, ic, tx):
            w.bind("<Button-1>", lambda e: command(), add="+")
            w.bind("<Enter>", enter, add="+")
            w.bind("<Leave>", leave, add="+")
        return item

    def _set_nav_active(self, key):
        for k, item in self.nav_items.items():
            bar, ic, tx = item._parts
            act = (k == key)
            item._active = act
            item.configure(fg_color=BG_CARD_HOVER if act else "transparent",
                           border_color=BORDER_STRONG if act else BG_PANEL)
            bar.configure(fg_color=BLUE_NEON if act else BG_PANEL)
            ic.configure(text_color=BLUE_NEON if act else TEXT_MUTED)
            tx.configure(text_color=TEXT_MAIN if act else TEXT_MUTED)

    # ------------------- STATUS BAR --------------------------------------------
    def build_statusbar(self, parent):
        bar = ctk.CTkFrame(parent, fg_color=BG_PANEL, corner_radius=0, height=34)
        bar.pack(side="bottom", fill="x")
        bar.pack_propagate(False)
        ctk.CTkFrame(parent, fg_color=BORDER_SOFT, height=1, corner_radius=0).pack(side="bottom", fill="x")
        self.sb_dot = ctk.CTkLabel(bar, text="●", font=(F_BODY, 12), text_color=TEXT_DIM, width=14)
        self.sb_dot.pack(side="left", padx=(22, 6))
        self.sb_text = ctk.CTkLabel(bar, text="Aguardando verificação", font=(F_BODY, 11), text_color=TEXT_MUTED)
        self.sb_text.pack(side="left")
        self.sb_integrity = ctk.CTkLabel(bar, text="Segura", font=(F_SEMI, 11), text_color=SEV_OK)
        self.sb_integrity.pack(side="right", padx=(4, 22))
        ctk.CTkLabel(bar, text="Integridade do sistema:", font=(F_BODY, 11), text_color=TEXT_MUTED).pack(side="right")
        self.sb_int_dot = ctk.CTkLabel(bar, text="●", font=(F_BODY, 12), text_color=SEV_OK, width=14)
        self.sb_int_dot.pack(side="right", padx=(0, 6))
        self.sb_sys = ctk.CTkLabel(bar, text="CPU 0%   RAM 0%", font=(F_MONO, 11), text_color=TEXT_DIM)
        self.sb_sys.pack(side="right", padx=26)
        if not self.is_admin:
            ctk.CTkLabel(bar, text="  •  Sem admin: pastas protegidas não serão totalmente verificadas",
                         font=(F_BODY, 11), text_color=SEV_HIGH).pack(side="left")

    # ------------------- COMPONENTES -----------------------------------------
    def card(self, parent, fg=BG_CARD, border=BORDER_SOFT, radius=14, **kw):
        return ctk.CTkFrame(parent, fg_color=fg, corner_radius=radius, border_width=1, border_color=border, **kw)

    def section_title(self, parent, text, icon=None, color=TEXT_MAIN):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        if icon:
            ctk.CTkLabel(row, text=self.ic(icon), font=self.icon_font(16), text_color=SEV_CRITICAL if icon == "warn" else BLUE_NEON).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(row, text=text, font=(F_HEAD, 15), text_color=color).pack(side="left")
        return row

    def sev_badge(self, parent, sev, width=74):
        bg, fg = SEV_BADGE.get(sev, SEV_BADGE["LOW"])
        return ctk.CTkLabel(parent, text=SEV_LABELS.get(sev, sev), font=(F_SEMI, 11), width=width, height=22,
                            fg_color=bg, corner_radius=11, text_color=fg)

    def page_header(self, parent, icon, title, subtitle=""):
        head = self.card(parent, fg=BG_PANEL)
        head.pack(fill="x", padx=28, pady=(24, 14))
        hin = ctk.CTkFrame(head, fg_color="transparent")
        hin.pack(fill="x", padx=22, pady=16)
        ctk.CTkLabel(hin, text=self.ic(icon), font=self.icon_font(26), text_color=BLUE_NEON).pack(side="left", padx=(0, 14))
        tbox = ctk.CTkFrame(hin, fg_color="transparent")
        tbox.pack(side="left")
        ctk.CTkLabel(tbox, text=title, font=(F_HEAD, 22), text_color=TEXT_MAIN, height=28).pack(anchor="w")
        sub = ctk.CTkLabel(tbox, text=subtitle, font=(F_BODY, 12), text_color=TEXT_MUTED, height=18)
        sub.pack(anchor="w")
        right = ctk.CTkFrame(hin, fg_color="transparent")
        right.pack(side="right")
        return head, right, sub

    def ghost_btn(self, parent, text, icon, command, width=130, height=36, color=BLUE_GLOW):
        return ctk.CTkButton(parent, text=f"{text}", width=width, height=height, corner_radius=9,
                             font=(F_SEMI, 12), fg_color=BG_CARD, hover_color=BG_CARD_HOVER,
                             text_color=color, border_width=1, border_color=BORDER_STRONG, command=command)

    def _card_hover(self, card, widgets, fg=BG_CARD, fg_hi=BG_CARD_HOVER, bd=BORDER_SOFT, bd_hi=BORDER_GLOW, click=None):
        """Realce de borda ao passar o mouse (sem piscar entre os filhos do cartão)."""
        def _in(_e=None):
            try:
                card.configure(fg_color=fg_hi, border_color=bd_hi)
            except Exception:
                pass

        def _check_out():
            try:
                x, y = card.winfo_pointerxy()
                over = card.winfo_containing(x, y)
                while over is not None:
                    if over == card:
                        return
                    over = over.master
                card.configure(fg_color=fg, border_color=bd)
            except Exception:
                pass

        def _out(_e=None):
            card.after(15, _check_out)

        for w in widgets:
            if w is None:
                continue
            try:
                w.bind("<Enter>", _in, add="+")
                w.bind("<Leave>", _out, add="+")
                if click is not None:
                    w.bind("<Button-1>", click, add="+")
                    w.configure(cursor="hand2")
            except Exception:
                pass

    def _descendants(self, widget):
        out = [widget]
        try:
            for ch in widget.winfo_children():
                if isinstance(ch, (ctk.CTkBaseClass,)):
                    out.extend(self._descendants(ch))
        except Exception:
            pass
        return out

    def copy_text(self, text):
        try:
            self.clipboard_clear()
            self.clipboard_append(text or "")
            self.update_idletasks()
            return True
        except Exception:
            return False

    # ------------------- DASHBOARD -----------------------------------------------
    def build_dashboard(self):
        self.dash = ctk.CTkFrame(self.stage, fg_color="transparent")
        self.dash_banner = BgCanvas(self.dash, self.whale_img, anchor=(0.6, 0.42), height=self.S(168),
                                    overlay=lambda img, w, h: shade_bottom(shade_horizontal(img, stop=0.6), strength=0.9, height=0.35),
                                    layout=self._dash_banner_layout)
        self.dash_banner.pack(fill="x")
        if not self.is_admin:
            adm = ctk.CTkButton(self.dash, text="Reabrir como Admin", font=(F_SEMI, 12), width=170, height=32,
                                corner_radius=16, fg_color=AMBER_BG, hover_color="#222222", text_color=SEV_MEDIUM,
                                border_width=1, border_color=AMBER_BD, command=self._elevate)
            adm.place(relx=1.0, x=-24, y=18, anchor="ne")
            Tooltip(adm, "Sem administrador, pastas protegidas (System32, Program Files, Prefetch) não são totalmente verificadas.")

        body = ctk.CTkFrame(self.dash, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=26, pady=(4, 16))
        body.grid_columnconfigure(0, weight=5, uniform="d")
        body.grid_columnconfigure(1, weight=2, uniform="d")
        body.grid_rowconfigure(0, weight=5)
        body.grid_rowconfigure(1, weight=4)

        self._build_scan_card(body)
        self._build_side_stats(body)
        self._build_recent_table(body)
        self._build_quote_card(body)

    def _dash_banner_layout(self, c, w, h):
        s = self.S
        c.create_text(s(30), s(30), text="Bem-vindo ao", anchor="w", fill=TEXT_MAIN, font=(F_HEAD_LIGHT, -s(24)))
        tf = tkfont.Font(family=F_HEAD, size=-s(44))
        c.create_text(s(28), s(74), text="CELESTIAL", anchor="w", fill="#FFFFFF", font=tf)
        c.create_text(s(28) + tf.measure("CELESTIAL "), s(74), text="SCAN", anchor="w", fill=BLUE_NEON, font=tf)
        c.create_text(s(30), s(116), anchor="nw", fill=TEXT_MUTED, font=(F_BODY, -s(14)),
                      text="Verifique o sistema em busca de comportamentos e arquivos suspeitos.\nTransparência para um jogo mais justo.")
        top = s(62) if not self.is_admin else s(62)
        c.create_text(w - s(30), top, anchor="ne", justify="right", fill=TEXT_MUTED, font=(F_BODY, -s(11)),
                      text="DETECTA\nANALISA\nPROTEGE\nJOGO LIMPO SEMPRE")
        c.create_line(w - s(60), top + s(78), w - s(30), top + s(78), fill=BLUE_NEON, width=2)

    def _build_scan_card(self, body):
        card = self.card(body)
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=(0, 10))
        head = ctk.CTkFrame(card, fg_color="transparent")
        head.pack(fill="x", padx=20, pady=(14, 0))
        self.scan_title = ctk.CTkLabel(head, text="ESCANEAMENTO", font=(F_HEAD, 16), text_color=TEXT_MAIN)
        self.scan_title.pack(side="left")
        self.start_btn = GlowButton(head, text="▶  INICIAR SCAN", width=190, height=36, glow=True,
                                    command=self.start_scan)
        self.start_btn.pack(side="right")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=(6, 12))
        left = ctk.CTkFrame(inner, fg_color="transparent")
        left.pack(side="left", fill="y", padx=(4, 10))
        self.ring = tk.Canvas(left, width=self.S(186), height=self.S(186), bg=BG_CARD,
                              highlightthickness=0, bd=0)
        self.ring.pack(pady=(4, 2))
        self.ring_sub = ctk.CTkLabel(left, text="Pronto para iniciar.", font=(F_BODY, 12),
                                     text_color=TEXT_MUTED, wraplength=230, height=18)
        self.ring_sub.pack()
        self.ring_hint = ctk.CTkLabel(left, text="Clique em INICIAR SCAN para começar.",
                                      font=(F_BODY, 11), text_color=TEXT_DIM, height=16)
        self.ring_hint.pack()
        self._draw_ring(0)

        stages = ctk.CTkFrame(inner, fg_color="transparent")
        stages.pack(side="left", fill="both", expand=True, padx=(16, 6))
        self.stage_rows = []
        for name in SCAN_STAGES:
            r = ctk.CTkFrame(stages, fg_color="transparent", height=26)
            r.pack(fill="x", pady=1)
            r.pack_propagate(False)
            ic = ctk.CTkLabel(r, text=self.ic("clock"), font=self.icon_font(14), text_color=TEXT_DIM, width=26)
            ic.pack(side="left")
            ctk.CTkLabel(r, text=name, font=(F_BODY, 13), text_color=TEXT_MAIN).pack(side="left", padx=(8, 0))
            st = ctk.CTkLabel(r, text="Pendente", font=(F_BODY, 12), text_color=TEXT_DIM, width=96, anchor="w")
            st.pack(side="right")
            self.stage_rows.append((ic, st))

    def _draw_ring(self, p):
        c = self.ring
        c.delete("all")
        s = self.S
        size = s(186)
        pad = s(18)
        c.create_oval(pad - s(6), pad - s(6), size - pad + s(6), size - pad + s(6), outline="#262626", width=1)
        c.create_arc(pad, pad, size - pad, size - pad, start=90, extent=-359.9, style="arc",
                     outline="#1E1E1E", width=s(12))
        if p > 0.001:
            ext = -359.9 * min(1.0, p)
            col = BLUE_NEON
            if self.total_detections and self._has_critical():
                col = "#FFFFFF"
            c.create_arc(pad, pad, size - pad, size - pad, start=90, extent=ext, style="arc",
                         outline="#3A3A3A", width=s(20))
            c.create_arc(pad, pad, size - pad, size - pad, start=90, extent=ext, style="arc",
                         outline=col, width=s(10))
        c.create_text(size // 2, size // 2 - s(4), text=f"{int(p * 100)}%", fill=TEXT_MAIN, font=(F_HEAD, -s(38)))
        c.create_text(size // 2, size // 2 + s(28), text="PROGRESSO", fill=TEXT_DIM, font=(F_BODY, -s(9)))

    def _build_side_stats(self, body):
        col = ctk.CTkFrame(body, fg_color="transparent")
        col.grid(row=0, column=1, sticky="nsew", pady=(0, 10))
        self.det_card, self.det_num = self._big_stat(col, "warn", "ITENS DETECTADOS", "Possíveis indícios de trapaça",
                                                     SEV_CRITICAL, RED_BG, RED_BD, lambda e=None: self.show_view("result"))
        self.det_card.pack(fill="x", pady=(0, 8))
        self.clean_card, self.clean_num = self._big_stat(col, "check", "ITENS LIMPOS", "Nenhuma anomalia encontrada",
                                                         TEXT_ON_LIGHT, GREEN_BG, GREEN_BD, lambda e=None: self.show_view("logs"),
                                                         sub_color="#3A3A3A")
        self.clean_card.pack(fill="x", pady=(0, 8))
        row = ctk.CTkFrame(col, fg_color="transparent")
        row.pack(fill="both", expand=True)
        row.grid_columnconfigure((0, 1), weight=1, uniform="s")
        row.grid_rowconfigure(0, weight=1)
        self.time_lbl = self._mini_stat(row, "stopwatch", "TEMPO", "00:00", 0)
        self.files_lbl = self._mini_stat(row, "library", "ANALISADOS", "0", 1)

    def _big_stat(self, parent, icon, title, sub, color, bg, bd, click, sub_color=TEXT_MUTED):
        card = self.card(parent, fg=bg, border=bd)
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=10)
        ic = ctk.CTkLabel(inner, text=self.ic(icon), font=self.icon_font(30), text_color=color, width=44)
        ic.pack(side="left", padx=(0, 12))
        box = ctk.CTkFrame(inner, fg_color="transparent")
        box.pack(side="left", fill="x", expand=True)
        num = ctk.CTkLabel(box, text="0", font=(F_HEAD, 26), text_color=color, height=30)
        num.pack(anchor="w")
        t = ctk.CTkLabel(box, text=title, font=(F_HEAD, 13), text_color=color, height=16)
        t.pack(anchor="w")
        s = ctk.CTkLabel(box, text=sub, font=(F_BODY, 11), text_color=sub_color, height=16)
        s.pack(anchor="w")
        ch = ctk.CTkLabel(inner, text=self.ic("chevron"), font=self.icon_font(14), text_color=sub_color)
        ch.pack(side="right")
        self._card_hover(card, [card, inner, ic, box, num, t, s, ch], fg=bg, fg_hi=bg, bd=bd, bd_hi=color, click=click)
        return card, num

    def _mini_stat(self, parent, icon, title, value, col):
        card = self.card(parent)
        card.grid(row=0, column=col, sticky="nsew", padx=(0, 4) if col == 0 else (4, 0))
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", expand=True, padx=12, pady=10)
        top = ctk.CTkFrame(inner, fg_color="transparent")
        top.pack(fill="x")
        ctk.CTkLabel(top, text=self.ic(icon), font=self.icon_font(16), text_color=BLUE_BRIGHT, width=20).pack(side="left", padx=(0, 6))
        ctk.CTkLabel(top, text=title, font=(F_BODY, 10), text_color=TEXT_MUTED, height=16).pack(side="left")
        val = ctk.CTkLabel(inner, text=value, font=(F_HEAD, 26), text_color=TEXT_MAIN, height=34)
        val.pack(anchor="w", pady=(6, 0))
        self._card_hover(card, self._descendants(card))
        return val

    def _build_recent_table(self, body):
        card = self.card(body)
        card.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        head = ctk.CTkFrame(card, fg_color="transparent")
        head.pack(fill="x", padx=18, pady=(12, 6))
        self.section_title(head, "ÚLTIMAS DETECÇÕES", icon="warn").pack(side="left")
        link = ctk.CTkLabel(head, text="Ver todos", font=(F_BODY, 12), text_color=BLUE_NEON, cursor="hand2")
        link.pack(side="right")
        link.bind("<Button-1>", lambda e: self.show_view("logs"), add="+")

        table = ctk.CTkFrame(card, fg_color="#0B0B0B", corner_radius=10)
        table.pack(fill="both", expand=True, padx=14, pady=(0, 12))
        cols = [("NOME", 3), ("CATEGORIA", 2), ("CAMINHO", 5), ("RISCO", 2), ("DETECTADO EM", 2)]
        hdr = ctk.CTkFrame(table, fg_color="#141414", corner_radius=8, height=28)
        hdr.pack(fill="x", padx=4, pady=(4, 2))
        self._table_cols(hdr)
        for i, (t, _) in enumerate(cols):
            ctk.CTkLabel(hdr, text=t, font=(F_SEMI, 10), text_color=TEXT_MUTED, anchor="w").grid(row=0, column=i, sticky="w", padx=10, pady=4)
        self.recent_rows = []
        for _ in range(5):
            r = ctk.CTkFrame(table, fg_color="transparent", height=30, cursor="hand2")
            self._table_cols(r)
            name = ctk.CTkLabel(r, text="", font=(F_SEMI, 12), text_color=TEXT_MAIN, anchor="w")
            cat = ctk.CTkLabel(r, text="", font=(F_BODY, 12), text_color=TEXT_MUTED, anchor="w")
            path = ctk.CTkLabel(r, text="", font=(F_MONO, 11), text_color=TEXT_MUTED, anchor="w")
            sev = self.sev_badge(r, "LOW")
            when = ctk.CTkLabel(r, text="", font=(F_BODY, 12), text_color=TEXT_MUTED, anchor="w")
            r._item = None
            for i, w in enumerate((name, cat, path, sev, when)):
                w.grid(row=0, column=i, sticky="w", padx=10, pady=3)
            for w in (r, name, cat, path, sev, when):
                w.bind("<Button-1>", lambda e, row=r: row._item and self.open_detail(row._item), add="+")
            self.recent_rows.append((r, name, cat, path, sev, when))
        self.recent_empty = ctk.CTkLabel(table, text="Nenhuma detecção até agora.", font=(F_BODY, 12),
                                         text_color=TEXT_DIM)
        self.recent_empty.pack(pady=26)

    def _table_cols(self, frame):
        for i, wgt in enumerate((3, 2, 5, 2, 2)):
            frame.grid_columnconfigure(i, weight=wgt, uniform="t")

    def _build_quote_card(self, body):
        wrap = self.card(body, fg=BG_CARD)
        wrap.grid(row=1, column=1, sticky="nsew")

        def layout(c, w, h):
            s = self.S
            c.create_text(s(18), s(20), anchor="nw", fill=TEXT_MAIN, font=(F_HEAD, -s(15)),
                          text="“ÁGUAS PROFUNDAS\nREVELAM A VERDADE.”")
            c.create_text(s(18), h - s(44), anchor="w", fill=TEXT_MAIN, font=(F_HEAD, -s(14)), text="CELESTIAL SCAN")
            c.create_text(s(18), h - s(26), anchor="w", fill=TEXT_MUTED, font=(F_BODY, -s(10)), text="ANTI-CHEAT")
            c.create_line(s(18), h - s(12), s(48), h - s(12), fill=BLUE_NEON, width=2)

        def overlay(img, w, h):
            img = shade_bottom(img, strength=0.75, height=0.5)
            top = Image.new("RGBA", img.size, (0, 0, 0, 0))
            ImageDraw.Draw(top).rectangle((0, 0, w, int(h * 0.45)), fill=(5, 5, 5, 120))
            return Image.alpha_composite(img, top.filter(ImageFilter.GaussianBlur(30)))

        self.quote = BgCanvas(wrap, self.ocean_img, anchor=(0.85, 0.9), overlay=overlay, layout=layout, bg=BG_CARD)
        self.quote.pack(fill="both", expand=True, padx=2, pady=2)

    # ------------------- RESULTADO ---------------------------------------------
    def build_result(self):
        self.result_view = ctk.CTkFrame(self.stage, fg_color="transparent")
        self.result_banner = BgCanvas(self.result_view, self.whale_img, anchor=(0.55, 0.38), height=self.S(150),
                                      overlay=self._result_overlay, layout=self._result_layout)
        self.result_banner.pack(fill="x")

        grid = ctk.CTkFrame(self.result_view, fg_color="transparent")
        grid.pack(fill="both", expand=True, padx=24, pady=(6, 10))
        self.cat_cards = {}
        for i, cat in enumerate(LOG_CATEGORIES):
            r, c = divmod(i, 5)
            grid.grid_columnconfigure(c, weight=1, uniform="cards")
            grid.grid_rowconfigure(r, weight=1, uniform="rows")
            self.cat_cards[cat] = self._category_card(grid, cat, r, c)

        foot = self.card(self.result_view)
        foot.pack(fill="x", padx=24, pady=(0, 16))
        fin = ctk.CTkFrame(foot, fg_color="transparent")
        fin.pack(fill="x", padx=18, pady=10)
        ctk.CTkLabel(fin, text=self.ic("shield"), font=self.icon_font(26), text_color=BLUE_NEON).pack(side="left", padx=(0, 12))
        tb = ctk.CTkFrame(fin, fg_color="transparent")
        tb.pack(side="left")
        btns = ctk.CTkFrame(tb, fg_color="transparent")
        btns.pack(anchor="w")
        for txt, cmd in [("Falar com Suporte", lambda: webbrowser.open(DISCORD_LINK)),
                         ("Discord", lambda: webbrowser.open(DISCORD_LINK))]:
            ctk.CTkButton(btns, text=txt, font=(F_BODY, 14), fg_color="transparent", hover_color=BG_CARD_HOVER,
                          text_color=TEXT_MAIN, width=10, height=28, corner_radius=8, command=cmd).pack(side="left", padx=(0, 6))
        self.copy_result_btn = ctk.CTkButton(btns, text="Copiar resultado", font=(F_BODY, 14), fg_color="transparent",
                                             hover_color=BG_CARD_HOVER, text_color=TEXT_MAIN, width=10, height=28,
                                             corner_radius=8, command=self._copy_result)
        self.copy_result_btn.pack(side="left")
        ctk.CTkLabel(tb, text=spaced("O CELESTIAL SCAN TRABALHA PARA UM AMBIENTE JUSTO E LIMPO."),
                     font=(F_BODY, 8), text_color=TEXT_DIM, height=12).pack(anchor="w", padx=10)
        self.new_scan_btn = GlowButton(fin, text="↻  Nova Verificação", width=210, height=42,
                                       command=self.new_scan)
        self.new_scan_btn.pack(side="right")

    def _result_state(self):
        with self._lock:
            snap = {c: list(v) for c, v in self.logs_data.items()}
        total = self.total_detections
        det = [it for c in DETECTION_CATEGORIES for it in snap.get(c, [])]
        crit = sum(1 for it in det if it.get("severity") == "CRITICAL")
        high = sum(1 for it in det if it.get("severity") == "HIGH")
        top_reason = ""
        for cat in ["Ameaças", "Mods", "Autoclickers", "Bypass"]:
            for it in snap.get(cat, []):
                if it.get("severity") == "CRITICAL":
                    top_reason = it.get("name", "")
                    break
            if top_reason:
                break
        return snap, total, crit, high, top_reason

    def _verdict(self):
        _, total, crit, high, top = self._result_state()
        if self._stage < 0 and not self._scan_finished:
            return "AGUARDANDO VERIFICAÇÃO", "INICIE UM SCAN NO DASHBOARD", BLUE_NEON, "info", (38, 38, 38)
        if self.scanning:
            return "VERIFICAÇÃO EM ANDAMENTO", f"{total} ITEM(NS) ENCONTRADO(S) ATÉ AGORA", BLUE_NEON, "search", (38, 38, 38)
        el = self._elapsed_str()
        if total == 0:
            return "SISTEMA LIMPO", f"VERIFICAÇÃO CONCLUÍDA EM {el}", SEV_OK, "check", (60, 60, 60)
        if crit > 0:
            word = "AMEAÇA DETECTADA" if crit == 1 else "AMEAÇAS DETECTADAS"
            sub = f"CONCLUÍDA EM {el}  •  MOTIVO: {top[:38]}" if top else f"VERIFICAÇÃO CONCLUÍDA EM {el}"
            return f"{crit} {word}", sub, SEV_CRITICAL, "warn", (70, 70, 70)
        return "SUSPEITO", f"{total} ITEM(NS) PARA REVISÃO ({high} ALTO)  •  {el}", SEV_HIGH, "warn", (52, 52, 52)

    def _result_geom(self, w, h):
        bw, bh = self.S(470), self.S(84)
        x1 = max(self.S(330), w // 2 - bw // 2 + self.S(20))
        y1 = h // 2 - bh // 2
        return (x1, y1, x1 + bw, y1 + bh)

    def _result_overlay(self, img, w, h):
        img = shade_bottom(shade_horizontal(img, start=0.85, stop=0.5), strength=0.9, height=0.3)
        _, _, col, _, rgb = self._verdict()
        r, g, b = _hex_rgb(col)
        return glass_panel(img, self._result_geom(w, h), self.S(10), fill=rgb + (150,), outline=(r, g, b, 220),
                           width=2, glow=(r, g, b, 60))

    def _result_layout(self, c, w, h):
        s = self.S
        title, sub, col, icon, _ = self._verdict()
        # jogador
        c.create_oval(s(28), h // 2 - s(38), s(104), h // 2 + s(38), outline=BLUE_NEON, width=2, fill="#0D0D0D")
        c.create_text(s(66), h // 2, text=self.ic("people"), fill=BLUE_BRIGHT, font=self.icon_font(-s(28)))
        c.create_text(s(122), h // 2 - s(26), anchor="w", text=spaced("JOGADOR"), fill=TEXT_MUTED, font=(F_BODY, -s(10)))
        c.create_text(s(122), h // 2 + s(2), anchor="w", text=_safe_user()[:18], fill=TEXT_MAIN, font=(F_HEAD, -s(24)))
        c.create_text(s(122), h // 2 + s(28), anchor="w", text=platform.node()[:22], fill=TEXT_MUTED, font=(F_BODY, -s(11)))
        # veredito
        x1, y1, x2, y2 = self._result_geom(w, h)
        c.create_text(x1 + s(42), (y1 + y2) // 2, text=self.ic(icon), fill=col, font=self.icon_font(-s(34)))
        c.create_text(x1 + s(82), y1 + s(32), anchor="w", text=title, fill=col, font=(F_HEAD, -s(25)))
        c.create_text(x1 + s(83), y1 + s(60), anchor="w", text=sub, fill=TEXT_MUTED, font=(F_BODY, -s(10)))
        c.create_text(w - s(30), s(28), anchor="ne", justify="left", fill=TEXT_MUTED, font=(F_BODY, -s(10)),
                      text=spaced("PROTEGENDO") + "\n" + spaced("JOGADORES") + "\n" + spaced("EM TODO O MUNDO"))
        c.create_line(w - s(60), s(18), w - s(30), s(18), fill=BLUE_NEON, width=2)
        c.create_text(s(28), s(16), anchor="nw", text=spaced("MAIS JOGO. MENOS TRAPAÇA.", 1), fill=TEXT_DIM, font=(F_BODY, -s(10)))

    def _category_card(self, grid, cat, r, c):
        icon, title, desc = CATEGORY_INFO[cat]
        card = self.card(grid)
        card.grid(row=r, column=c, sticky="nsew", padx=5, pady=5)
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", expand=True, padx=14, pady=10)
        top = ctk.CTkFrame(inner, fg_color="transparent")
        top.pack(fill="x")
        ic = ctk.CTkLabel(top, text=self.ic(icon), font=self.icon_font(28), text_color=BLUE_BRIGHT)
        ic.pack(side="left")
        q = ctk.CTkLabel(top, text="?", font=(F_SEMI, 11), width=22, height=22, corner_radius=6,
                         fg_color="#1A1A1A", text_color=TEXT_MUTED)
        q.pack(side="right", anchor="n")
        Tooltip(q, desc)
        t = ctk.CTkLabel(inner, text=title, font=(F_SEMI, 14), text_color=TEXT_MAIN, anchor="w", height=20)
        t.pack(fill="x", pady=(6, 0))
        num = ctk.CTkLabel(inner, text="0", font=(F_HEAD, 28), text_color=TEXT_MAIN, anchor="w", height=32)
        num.pack(fill="x")
        cap = ctk.CTkLabel(inner, text=spaced("REGISTROS" if cat == "Sistema" else "ITENS ENCONTRADOS"),
                           font=(F_BODY, 8), text_color=TEXT_MUTED, anchor="w", height=12)
        cap.pack(fill="x")
        bottom = ctk.CTkFrame(inner, fg_color="transparent")
        bottom.pack(fill="x", pady=(8, 0))
        pill = ctk.CTkLabel(bottom, text="LIMPO", font=(F_HEAD, 11), width=88, height=26, corner_radius=8,
                            fg_color="#1A1A1A", text_color=SEV_OK)
        pill.pack(side="left")
        more = ctk.CTkLabel(bottom, text="Ver detalhes", font=(F_BODY, 10, "underline"), text_color=TEXT_MUTED, cursor="hand2")
        more.pack(side="right")
        open_cat = (lambda e=None, k=cat: self.open_category(k))
        more.bind("<Button-1>", open_cat, add="+")
        self._card_hover(card, [card, inner, top, ic, t, num, cap, bottom, pill], click=open_cat)
        return {"num": num, "pill": pill}

    def open_category(self, cat):
        self.current_category = cat
        self.show_view("logs")

    def render_result(self):
        snap, total, crit, high, top = self._result_state()
        for cat, refs in self.cat_cards.items():
            items = snap.get(cat, [])
            n = len(items)
            refs["num"].configure(text=f"{n:,}".replace(",", "."))
            sevs = {it.get("severity", "LOW") for it in items}
            if cat == "Sistema":
                txt, fg, tc = ("INFO", BLUE_BG, BLUE_NEON)
            elif cat == "USB":
                txt, fg, tc = ("INFO", BLUE_BG, BLUE_NEON) if items else ("LIMPO", "#1A1A1A", SEV_OK)
            elif "CRITICAL" in sevs or "HIGH" in sevs:
                txt, fg, tc = ("DETECTADO", "#F2F2F2", TEXT_ON_LIGHT)
            elif "MEDIUM" in sevs:
                txt, fg, tc = ("SUSPEITO", "#3A3A3A", "#F2F2F2")
            elif items:
                txt, fg, tc = ("REVISAR", "#1A1A1A", SEV_MEDIUM)
            else:
                txt, fg, tc = ("LIMPO", "#1A1A1A", SEV_OK)
            refs["pill"].configure(text=("✓  " if txt == "LIMPO" else "!  ") + txt if txt != "INFO" else "INFO",
                                   fg_color=fg, text_color=tc)
        self.result_banner.refresh()

    def _copy_result(self):
        snap, total, crit, high, top = self._result_state()
        title, sub, _, _, _ = self._verdict()
        lines = [f"{APP_NAME} {VERSION} — Resultado", f"Usuário: {_safe_user()}", f"Veredito: {title} — {sub}", ""]
        for cat in ["Ameaças", "Autoclickers", "Bypass", "Mods", "Suspeitos", "Ocultos", "Textos", "Lixeira"]:
            items = snap.get(cat, [])
            if not items:
                continue
            lines.append(f"== {cat} ({len(items)}) ==")
            for it in items:
                lines.append(f"[{it.get('severity', 'LOW')}] {it.get('name', '?')} :: {it.get('path', '')}")
            lines.append("")
        ok = self.copy_text("\n".join(lines))
        self.copy_result_btn.configure(text="Copiado!" if ok else "Falhou ao copiar")
        self.after(1300, lambda: self.copy_result_btn.configure(text="Copiar resultado"))

    # ------------------- LOGS ---------------------------------------------------
    def build_logs(self):
        self.logs_view = ctk.CTkFrame(self.stage, fg_color="transparent")
        _, right, self.logs_sub = self.page_header(self.logs_view, "list", "LOGS DA VERIFICAÇÃO",
                                                   "Todos os itens encontrados, por categoria.")
        self.risk_lbl = ctk.CTkLabel(right, text="STATUS: AGUARDANDO", font=(F_HEAD, 14), text_color=TEXT_MUTED)
        self.risk_lbl.pack(side="right")

        body = ctk.CTkFrame(self.logs_view, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=28, pady=(0, 18))
        rail = self.card(body, fg=BG_PANEL, width=220)
        rail.pack(side="left", fill="y", padx=(0, 14))
        rail.pack_propagate(False)
        ctk.CTkLabel(rail, text="CATEGORIAS", font=(F_SEMI, 10), text_color=TEXT_DIM).pack(anchor="w", padx=18, pady=(16, 6))
        self.cat_btns = {}
        for cat in LOG_CATEGORIES:
            icon = CATEGORY_INFO[cat][0]
            row = ctk.CTkFrame(rail, fg_color="transparent", corner_radius=9, height=36, cursor="hand2")
            row.pack(fill="x", padx=10, pady=1)
            row.pack_propagate(False)
            ic = ctk.CTkLabel(row, text=self.ic(icon), font=self.icon_font(14), text_color=TEXT_MUTED, width=28, cursor="hand2")
            ic.pack(side="left", padx=(8, 4))
            tx = ctk.CTkLabel(row, text=cat, font=(F_BODY, 13), text_color=TEXT_MUTED, anchor="w", cursor="hand2")
            tx.pack(side="left", fill="x", expand=True)
            cnt = ctk.CTkLabel(row, text="0", font=(F_SEMI, 11), text_color=TEXT_DIM, width=34, cursor="hand2")
            cnt.pack(side="right", padx=6)
            for w in (row, ic, tx, cnt):
                w.bind("<Button-1>", lambda e, c=cat: self.filter_logs(c), add="+")
            self.cat_btns[cat] = (row, ic, tx, cnt)

        content = ctk.CTkFrame(body, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True)
        trow = ctk.CTkFrame(content, fg_color="transparent")
        trow.pack(fill="x", pady=(2, 10))
        self.log_title = ctk.CTkLabel(trow, text="Ameaças", font=(F_HEAD, 19), text_color=TEXT_MAIN)
        self.log_title.pack(side="left")
        self.log_count = ctk.CTkLabel(trow, text="0 registros", font=(F_BODY, 12), text_color=TEXT_DIM)
        self.log_count.pack(side="left", padx=12)
        self.log_scroll = ctk.CTkScrollableFrame(content, fg_color=BG_PANEL, corner_radius=14, border_width=1,
                                                 border_color=BORDER_SOFT)
        self.log_scroll.pack(fill="both", expand=True)
        self._more_btn = None

    def _refresh_log_counts(self):
        with self._lock:
            counts = {c: len(v) for c, v in self.logs_data.items()}
        for cat, (row, ic, tx, cnt) in self.cat_btns.items():
            act = cat == self.current_category
            n = counts.get(cat, 0)
            row.configure(fg_color=BG_CARD_HOVER if act else "transparent")
            ic.configure(text_color=BLUE_NEON if act else TEXT_MUTED)
            tx.configure(text_color=TEXT_MAIN if act else TEXT_MUTED)
            cnt.configure(text=str(n), text_color=BLUE_NEON if n and cat != "Sistema" else TEXT_DIM)

    def filter_logs(self, category):
        self.current_category = category
        self.log_title.configure(text=CATEGORY_INFO[category][1])
        with self._lock:
            items = list(self.logs_data.get(category, []))
        self._log_items = sorted(items, key=lambda it: SEV_RANK.get(it.get("severity", "LOW"), 3))
        self._log_rendered = 0
        self.log_count.configure(text=f"{len(items)} registro(s)")
        self._refresh_log_counts()
        for w in self.log_scroll.winfo_children():
            w.destroy()
        self._more_btn = None
        try:
            self.log_scroll._parent_canvas.yview_moveto(0)
        except Exception:
            pass
        if not items:
            empty = ctk.CTkFrame(self.log_scroll, fg_color="transparent")
            empty.pack(pady=80)
            ctk.CTkLabel(empty, text=self.ic("check"), font=self.icon_font(40), text_color=TEXT_DIM).pack()
            ctk.CTkLabel(empty, text="Nenhum registro nesta categoria", font=(F_BODY, 13), text_color=TEXT_DIM).pack(pady=8)
            return
        self._render_more_logs()

    def _render_more_logs(self, page=40):
        if self._more_btn is not None:
            self._more_btn.destroy()
            self._more_btn = None
        end = min(len(self._log_items), self._log_rendered + page)
        for it in self._log_items[self._log_rendered:end]:
            self.render_log_row(self.log_scroll, it)
        self._log_rendered = end
        left = len(self._log_items) - end
        if left > 0:
            self._more_btn = ctk.CTkButton(self.log_scroll, text=f"Carregar mais ({left} restantes)", height=36,
                                           corner_radius=9, font=(F_SEMI, 12), fg_color=BG_CARD,
                                           hover_color=BG_CARD_HOVER, text_color=BLUE_NEON, border_width=1,
                                           border_color=BORDER_STRONG, command=self._render_more_logs)
            self._more_btn.pack(pady=12)

    def file_actions(self, parent, path, big=False):
        """Botões 'Ir até o local do arquivo' e 'Abrir o xit' (desativados se o arquivo sumiu)."""
        exists = path_exists(path)
        h = 38 if big else 28
        fs = 13 if big else 11
        go = ctk.CTkButton(parent, text="Ir até o local do arquivo", height=h, corner_radius=8, font=(F_SEMI, fs),
                           fg_color="#F2F2F2", hover_color="#D6D6D6", text_color=TEXT_ON_LIGHT, border_width=1,
                           border_color=BLUE_MID, command=lambda: open_in_explorer(path))
        op = ctk.CTkButton(parent, text="Abrir o xit", height=h, corner_radius=8, font=(F_SEMI, fs),
                           fg_color=RED_BG, hover_color="#262626", text_color=SEV_CRITICAL, border_width=1,
                           border_color=RED_BD, command=lambda: self.confirm_open(path))
        cp = ctk.CTkButton(parent, text="Copiar caminho", height=h, corner_radius=8, font=(F_SEMI, fs),
                           fg_color=BG_CARD, hover_color=BG_CARD_HOVER, text_color=BLUE_GLOW, border_width=1,
                           border_color=BORDER_STRONG, command=lambda: self.copy_text(path))
        if not exists:
            go.configure(state="disabled", text_color_disabled=TEXT_DIM, fg_color="#121212", border_color=BORDER_SOFT)
            op.configure(state="disabled", text_color_disabled=TEXT_DIM, fg_color="#121212", border_color=BORDER_SOFT)
        if not path:
            cp.configure(state="disabled", text_color_disabled=TEXT_DIM)
        return go, op, cp, exists

    def render_log_row(self, parent, item):
        sev = item.get("severity", "LOW")
        col = SEV_COLORS.get(sev, SEV_LOW)
        card = self.card(parent, radius=12)
        card.pack(fill="x", padx=10, pady=5)
        ctk.CTkFrame(card, fg_color=col, width=4, height=10, corner_radius=3).pack(side="left", fill="y", padx=(6, 0), pady=10)
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(side="left", fill="both", expand=True, padx=14, pady=10)
        head = ctk.CTkFrame(inner, fg_color="transparent")
        head.pack(fill="x")
        name = ctk.CTkLabel(head, text=item.get("name", "?"), font=(F_SEMI, 14), text_color=TEXT_MAIN, anchor="w")
        name.pack(side="left")
        self.sev_badge(head, sev).pack(side="right")
        if item.get("time"):
            ctk.CTkLabel(head, text=f"Hoje {item['time'][:5]}", font=(F_BODY, 11), text_color=TEXT_DIM).pack(side="right", padx=10)
        parts = [inner, head, name]
        if item.get("desc"):
            d = ctk.CTkLabel(inner, text=item["desc"], font=(F_BODY, 12), text_color=TEXT_MUTED, justify="left",
                             anchor="w", wraplength=760)
            d.pack(fill="x", pady=(3, 0))
            parts.append(d)
        path = item.get("path", "")
        if path:
            ptxt = path if len(path) <= 110 else "…" + path[-108:]
            p = ctk.CTkLabel(inner, text=ptxt, font=(F_MONO, 11), text_color=TEXT_DIM, justify="left", anchor="w")
            p.pack(fill="x", pady=(3, 0))
            parts.append(p)
        if item.get("evidence"):
            ev = item["evidence"]
            ev = ev if len(ev) <= 140 else ev[:138] + "…"
            e = ctk.CTkLabel(inner, text=f"Evidência: {ev}", font=(F_MONO, 11), text_color=BLUE_BRIGHT, justify="left",
                             anchor="w", wraplength=760)
            e.pack(fill="x", pady=(2, 0))
            parts.append(e)
        if path:
            acts = ctk.CTkFrame(inner, fg_color="transparent")
            acts.pack(fill="x", pady=(8, 0))
            go, op, cp, exists = self.file_actions(acts, path)
            go.pack(side="left", padx=(0, 6))
            op.pack(side="left", padx=(0, 6))
            cp.pack(side="left")
            if not exists:
                ctk.CTkLabel(acts, text="arquivo não encontrado", font=(F_BODY, 11), text_color=TEXT_DIM).pack(side="left", padx=10)
            det = ctk.CTkLabel(acts, text="Ver detalhes", font=(F_BODY, 11, "underline"), text_color=BLUE_NEON, cursor="hand2")
            det.pack(side="right")
            det.bind("<Button-1>", lambda e, it=item: self.open_detail(it), add="+")
        self._card_hover(card, [card] + parts, click=lambda e, it=item: self.open_detail(it))

    # ------------------- DETALHE + CONFIRMAÇÃO ----------------------------------
    def _modal(self, title, geometry):
        win = ctk.CTkToplevel(self)
        win.title(title)
        win.geometry(geometry)
        win.configure(fg_color=BG_DEEP)
        win.transient(self)
        win.after(270, lambda: self._apply_icon(win))

        def _focus():
            try:
                win.lift()
                win.focus_force()
                win.grab_set()
            except Exception:
                pass
        win.after(150, _focus)
        return win

    def open_detail(self, it):
        sev = it.get("severity", "LOW")
        col = SEV_COLORS.get(sev, SEV_LOW)
        path = it.get("path", "")
        win = self._modal("Detalhe do achado", "680x560")
        head = self.card(win, fg=BG_PANEL, border=col)
        head.pack(fill="x", padx=18, pady=(18, 10))
        hin = ctk.CTkFrame(head, fg_color="transparent")
        hin.pack(fill="x", padx=18, pady=14)
        ctk.CTkLabel(hin, text=it.get("name", "?"), font=(F_HEAD, 19), text_color=TEXT_MAIN, wraplength=520,
                     justify="left", anchor="w").pack(side="left", fill="x", expand=True)
        self.sev_badge(hin, sev, width=86).pack(side="right")

        body = ctk.CTkScrollableFrame(win, fg_color=BG_PANEL, corner_radius=14, border_width=1, border_color=BORDER_SOFT)
        body.pack(fill="both", expand=True, padx=18, pady=(0, 10))
        status = it.get("status") or (file_status(path) if path else "—")
        dt, size = file_meta(path) if path else ("—", "—")

        def field(titulo, valor, mono=True, color=TEXT_MUTED):
            ctk.CTkLabel(body, text=titulo, font=(F_SEMI, 10), text_color=TEXT_DIM).pack(anchor="w", padx=16, pady=(12, 0))
            ctk.CTkLabel(body, text=valor or "—", font=(F_MONO, 12) if mono else (F_BODY, 12),
                         text_color=color, justify="left", wraplength=580, anchor="w").pack(anchor="w", padx=16, pady=(2, 0))

        field("POR QUE FOI MARCADO (evidência)", it.get("evidence", "—"), color=BLUE_BRIGHT)
        field("DESCRIÇÃO", it.get("desc", "—"), mono=False)
        field("CAMINHO", path or "—")
        field("ESTADO", status, mono=False, color=(SEV_OK if status == "Ativo" else BLUE_NEON))
        field("MODIFICADO EM", dt, mono=False)
        field("TAMANHO", size, mono=False)
        if it.get("time"):
            field("DETECTADO EM", f"Hoje {it['time']}", mono=False)

        row = ctk.CTkFrame(win, fg_color="transparent")
        row.pack(fill="x", padx=18, pady=(0, 16))
        go, op, cp, exists = self.file_actions(row, path, big=True)
        go.pack(side="left", expand=True, fill="x", padx=(0, 5))
        op.pack(side="left", expand=True, fill="x", padx=5)
        cp.pack(side="left", expand=True, fill="x", padx=(5, 0))
        if path and not exists:
            ctk.CTkLabel(win, text="arquivo não encontrado — ele pode ter sido apagado ou é só um vestígio.",
                         font=(F_BODY, 11), text_color=TEXT_DIM).pack(pady=(0, 12))

    def confirm_open(self, path):
        if not path_exists(path):
            return
        win = self._modal("Abrir o xit?", "520x260")
        box = self.card(win, fg=BG_PANEL, border=RED_BD)
        box.pack(fill="both", expand=True, padx=18, pady=18)
        top = ctk.CTkFrame(box, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=(18, 6))
        ctk.CTkLabel(top, text=self.ic("warn"), font=self.icon_font(30), text_color=SEV_CRITICAL).pack(side="left", padx=(0, 14))
        ctk.CTkLabel(top, text="Abrir este arquivo?", font=(F_HEAD, 19), text_color=TEXT_MAIN).pack(side="left")
        ctk.CTkLabel(box, text="Abrir um arquivo de xit pode EXECUTAR o programa neste computador.\n"
                               "Só continue se você souber o que está fazendo.\n\n" + os.path.basename(path),
                     font=(F_BODY, 12), text_color=TEXT_MUTED, justify="left", wraplength=440).pack(anchor="w", padx=20)
        row = ctk.CTkFrame(box, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=(14, 16), side="bottom")

        def yes():
            win.destroy()
            if not open_file_default(path):
                self.sb_text.configure(text="Não foi possível abrir o arquivo.")

        ctk.CTkButton(row, text="Cancelar", height=38, corner_radius=8, font=(F_SEMI, 13), fg_color=BG_CARD,
                      hover_color=BG_CARD_HOVER, text_color=TEXT_MAIN, border_width=1, border_color=BORDER_STRONG,
                      command=win.destroy).pack(side="left", expand=True, fill="x", padx=(0, 6))
        ctk.CTkButton(row, text="Abrir mesmo assim", height=38, corner_radius=8, font=(F_SEMI, 13), fg_color="#F2F2F2",
                      hover_color="#D6D6D6", text_color="#0A0A0A", command=yes).pack(side="left", expand=True, fill="x", padx=(6, 0))

    # ------------------- STRING EXTRACTOR ---------------------------------------
    def build_extractor(self):
        self.extractor_view = ctk.CTkFrame(self.stage, fg_color="transparent")
        _, right, _ = self.page_header(self.extractor_view, "code", "STRING EXTRACTOR",
                                       "Analise um .jar / .exe / .dll — hash, strings e detecções.")
        GlowButton(right, text="Selecionar arquivo", width=200, height=40, command=self._pick_extract_file).pack(side="right")
        drop = self.card(self.extractor_view, height=96, cursor="hand2")
        drop.pack(fill="x", padx=28, pady=(0, 12))
        drop.pack_propagate(False)
        self._drop_lbl = ctk.CTkLabel(drop, text="Clique aqui ou em “Selecionar arquivo” para analisar um executável ou mod.",
                                      font=(F_BODY, 13), text_color=TEXT_MUTED, cursor="hand2")
        self._drop_lbl.pack(expand=True)
        self._card_hover(drop, [drop, self._drop_lbl], click=lambda e: self._pick_extract_file())
        self.extract_scroll = ctk.CTkScrollableFrame(self.extractor_view, fg_color=BG_PANEL, corner_radius=14,
                                                     border_width=1, border_color=BORDER_SOFT)
        self.extract_scroll.pack(fill="both", expand=True, padx=28, pady=(0, 18))
        ctk.CTkLabel(self.extract_scroll, text="Nenhum arquivo analisado ainda.", font=(F_BODY, 13),
                     text_color=TEXT_DIM).pack(pady=60)

    def _pick_extract_file(self):
        try:
            from tkinter import filedialog
            path = filedialog.askopenfilename(
                parent=self, title="Selecionar arquivo para análise",
                filetypes=[("Executáveis e mods", "*.jar *.exe *.dll *.sys *.scr *.bat *.cmd *.ps1"),
                           ("Todos os arquivos", "*.*")])
        except Exception:
            path = ""
        if not path:
            return
        self._drop_lbl.configure(text=f"Analisando: {os.path.basename(path)} …", text_color=BLUE_NEON)
        threading.Thread(target=self._do_extract, args=(path,), daemon=True).start()

    def _do_extract(self, path):
        try:
            res = analyze_single_file(path, custom_strings=list(self.custom_strings))
        except Exception as e:
            res = {"error": str(e)}
        self.ui(lambda: self._render_extract(res))

    def _render_extract(self, res):
        for w in self.extract_scroll.winfo_children():
            w.destroy()
        if res.get("error"):
            self._drop_lbl.configure(text="Falha na análise.", text_color=SEV_HIGH)
            ctk.CTkLabel(self.extract_scroll, text=f"Erro: {res['error']}", font=(F_BODY, 13),
                         text_color=SEV_HIGH).pack(pady=40)
            return
        self._drop_lbl.configure(text=f"{res['name']} analisado", text_color=SEV_OK)
        vc = self.card(self.extract_scroll, border=res["vcolor"])
        vc.pack(fill="x", padx=10, pady=(10, 12))
        vin = ctk.CTkFrame(vc, fg_color="transparent")
        vin.pack(fill="x", padx=18, pady=14)
        ctk.CTkLabel(vin, text=res["verdict"], font=(F_HEAD, 28), text_color=res["vcolor"]).pack(side="left")
        ctk.CTkLabel(vin, text=f"  {len(res['detections'])} detecção(ões) • {res['strings_total']} strings",
                     font=(F_BODY, 13), text_color=TEXT_MUTED).pack(side="left", padx=10)
        acts = ctk.CTkFrame(vin, fg_color="transparent")
        acts.pack(side="right")
        go, op, cp, _ = self.file_actions(acts, res["path"])
        go.pack(side="left", padx=3)
        op.pack(side="left", padx=3)

        meta = self.card(self.extract_scroll)
        meta.pack(fill="x", padx=10, pady=(0, 12))
        for lbl, val in [("ARQUIVO", res["name"]), ("MD5", res["md5"]), ("SHA256", res["sha256"]),
                         ("TAMANHO", res["size_h"]), ("MODIFICADO", res["modified"]), ("CAMINHO", res["path"])]:
            r = ctk.CTkFrame(meta, fg_color="transparent")
            r.pack(fill="x", padx=16, pady=3)
            ctk.CTkLabel(r, text=lbl, font=(F_SEMI, 10), text_color=TEXT_DIM, width=90, anchor="w").pack(side="left")
            ctk.CTkLabel(r, text=val, font=(F_MONO, 11), text_color=TEXT_MAIN, justify="left", wraplength=640,
                         anchor="w").pack(side="left", padx=8)
            r.bind("<Button-1>", lambda e, v=val: self.copy_text(v), add="+")

        if res["detections"]:
            ctk.CTkLabel(self.extract_scroll, text=f"DETECÇÕES ({len(res['detections'])})", font=(F_HEAD, 14),
                         text_color=TEXT_MAIN).pack(anchor="w", padx=14, pady=(6, 6))
            for d in sorted(res["detections"], key=lambda x: SEV_RANK.get(x["severity"], 3)):
                col = SEV_COLORS.get(d["severity"], SEV_LOW)
                card = self.card(self.extract_scroll, radius=12)
                card.pack(fill="x", padx=12, pady=4)
                ctk.CTkFrame(card, fg_color=col, width=4, height=10, corner_radius=3).pack(side="left", fill="y", padx=(6, 0), pady=8)
                inner = ctk.CTkFrame(card, fg_color="transparent")
                inner.pack(side="left", fill="both", expand=True, padx=12, pady=8)
                top = ctk.CTkFrame(inner, fg_color="transparent")
                top.pack(fill="x")
                ctk.CTkLabel(top, text=d["name"], font=(F_SEMI, 13), text_color=TEXT_MAIN).pack(side="left")
                self.sev_badge(top, d["severity"]).pack(side="right")
                ctk.CTkLabel(inner, text=f"Evidência: {d['evidence']}", font=(F_MONO, 11), text_color=BLUE_BRIGHT,
                             justify="left", wraplength=660, anchor="w").pack(fill="x", pady=(3, 0))
        else:
            ctk.CTkLabel(self.extract_scroll, text="Nenhuma assinatura de xit encontrada neste arquivo.",
                         font=(F_SEMI, 13), text_color=SEV_OK).pack(pady=24)

    # ------------------- STRINGS PERSONALIZADAS ---------------------------------
    def build_strings(self):
        self.strings_view = ctk.CTkFrame(self.stage, fg_color="transparent")
        _, right, self.strings_status = self.page_header(self.strings_view, "tag", "STRINGS PERSONALIZADAS", "")
        for txt, cmd, w in [("Importar", self._import_strings, 100), ("Exportar", self._export_strings, 100),
                            ("Converter antigo", self._convert_old_strings, 150)]:
            self.ghost_btn(right, txt, None, cmd, width=w).pack(side="left", padx=4)

        form = self.card(self.strings_view, fg=BG_PANEL)
        form.pack(fill="x", padx=28, pady=(0, 12))
        fin = ctk.CTkFrame(form, fg_color="transparent")
        fin.pack(fill="x", padx=18, pady=14)
        ent = dict(fg_color=BG_CARD, border_color=BORDER_STRONG, text_color=TEXT_MAIN, height=36, corner_radius=8,
                   font=(F_BODY, 13))
        self.cs_process = ctk.CTkEntry(fin, placeholder_text="Processo (ex: javaw.exe)", width=190, **ent)
        self.cs_process.pack(side="left", padx=4)
        self.cs_client = ctk.CTkEntry(fin, placeholder_text="Nome do cliente", width=170, **ent)
        self.cs_client.pack(side="left", padx=4)
        self.cs_string = ctk.CTkEntry(fin, placeholder_text="String a detectar", width=230, **ent)
        self.cs_string.pack(side="left", padx=4)
        self.cs_string.bind("<Return>", lambda e: self._add_custom_string())
        self.cs_sev = ctk.CTkOptionMenu(fin, values=["CRITICAL", "HIGH", "MEDIUM", "LOW"], width=120, height=36,
                                        fg_color=BG_CARD, button_color=BLUE_DEEP, button_hover_color=BLUE_MID,
                                        dropdown_fg_color=BG_CARD, font=(F_BODY, 13))
        self.cs_sev.set("HIGH")
        self.cs_sev.pack(side="left", padx=4)
        GlowButton(fin, text="+ Adicionar", width=120, height=36, command=self._add_custom_string).pack(side="left", padx=6)

        self.strings_scroll = ctk.CTkScrollableFrame(self.strings_view, fg_color=BG_PANEL, corner_radius=14,
                                                     border_width=1, border_color=BORDER_SOFT)
        self.strings_scroll.pack(fill="both", expand=True, padx=28, pady=(0, 18))

    def render_custom_strings(self, status=None, color=TEXT_MUTED):
        self.strings_status.configure(
            text=status or f"{len(self.custom_strings)} string(s) • aplicadas em todo scan, extractor e presença",
            text_color=color)
        for w in self.strings_scroll.winfo_children():
            w.destroy()
        if not self.custom_strings:
            ctk.CTkLabel(self.strings_scroll, text="Nenhuma string personalizada. Adicione acima.", font=(F_BODY, 13),
                         text_color=TEXT_DIM).pack(pady=50)
            return
        for idx, cs in enumerate(self.custom_strings):
            card = self.card(self.strings_scroll, radius=12)
            card.pack(fill="x", padx=10, pady=4)
            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="x", padx=14, pady=9)
            self.sev_badge(inner, cs.get("severity", "HIGH")).pack(side="left")
            ctk.CTkLabel(inner, text=cs.get("string", ""), font=(F_MONO, 13), text_color=TEXT_MAIN).pack(side="left", padx=12)
            meta = f"{cs.get('client') or '—'}  •  processo: {cs.get('process') or 'qualquer'}"
            ctk.CTkLabel(inner, text=meta, font=(F_BODY, 12), text_color=TEXT_MUTED).pack(side="left", padx=8)
            ctk.CTkButton(inner, text="Remover", width=80, height=28, corner_radius=8, font=(F_SEMI, 11),
                          fg_color=RED_BG, hover_color="#262626", text_color=SEV_CRITICAL, border_width=1,
                          border_color=RED_BD, command=lambda i=idx: self._remove_custom_string(i)).pack(side="right")

    def _add_custom_string(self):
        val = self.cs_string.get().strip()
        if not val:
            self.render_custom_strings("Digite a string a detectar.", SEV_HIGH)
            return
        self.custom_strings.append({"process": self.cs_process.get().strip(), "client": self.cs_client.get().strip(),
                                    "string": val, "severity": self.cs_sev.get()})
        save_custom_strings(self.custom_strings)
        for e in (self.cs_process, self.cs_client, self.cs_string):
            e.delete(0, "end")
        self.render_custom_strings()

    def _remove_custom_string(self, idx):
        if 0 <= idx < len(self.custom_strings):
            self.custom_strings.pop(idx)
            save_custom_strings(self.custom_strings)
        self.render_custom_strings()

    def _import_strings(self):
        try:
            from tkinter import filedialog
            path = filedialog.askopenfilename(parent=self, title="Importar strings (JSON)",
                                              filetypes=[("JSON", "*.json"), ("Todos", "*.*")])
        except Exception:
            path = ""
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                raise ValueError("o arquivo precisa ser uma lista JSON")
            added = 0
            existing = {(c.get("string"), c.get("process")) for c in self.custom_strings}
            for d in data:
                if isinstance(d, dict) and d.get("string"):
                    key = (d.get("string"), d.get("process", ""))
                    if key in existing:
                        continue
                    existing.add(key)
                    self.custom_strings.append({"process": d.get("process", ""), "client": d.get("client", ""),
                                                "string": d.get("string", ""),
                                                "severity": (d.get("severity") or "HIGH").upper()})
                    added += 1
            save_custom_strings(self.custom_strings)
            self.render_custom_strings(f"Importadas {added} nova(s) string(s).", SEV_OK)
        except Exception as e:
            self.render_custom_strings(f"Erro ao importar: {e}", SEV_HIGH)

    def _export_strings(self):
        try:
            from tkinter import filedialog
            path = filedialog.asksaveasfilename(parent=self, title="Exportar strings (JSON)", defaultextension=".json",
                                                filetypes=[("JSON", "*.json")])
        except Exception:
            path = ""
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.custom_strings, f, ensure_ascii=False, indent=2)
            self.render_custom_strings(f"Exportado para {os.path.basename(path)}", SEV_OK)
        except Exception as e:
            self.render_custom_strings(f"Erro ao exportar: {e}", SEV_HIGH)

    def _convert_old_strings(self):
        win = self._modal("Converter formato antigo → JSON", "580x480")
        ctk.CTkLabel(win, text="Cole no formato  cliente:string  (uma por linha)", font=(F_SEMI, 13),
                     text_color=TEXT_MAIN).pack(anchor="w", padx=18, pady=(18, 6))
        box = ctk.CTkTextbox(win, fg_color=BG_CARD, border_width=1, border_color=BORDER_STRONG, text_color=TEXT_MAIN,
                             font=(F_MONO, 12))
        box.pack(fill="both", expand=True, padx=18, pady=(0, 10))

        def _do():
            parsed = parse_old_strings_format(box.get("1.0", "end"))
            existing = {(c.get("string"), c.get("process")) for c in self.custom_strings}
            added = 0
            for d in parsed:
                if (d["string"], d["process"]) in existing:
                    continue
                existing.add((d["string"], d["process"]))
                self.custom_strings.append(d)
                added += 1
            save_custom_strings(self.custom_strings)
            win.destroy()
            self.render_custom_strings(f"Convertidas e adicionadas {added} string(s).", SEV_OK)

        GlowButton(win, text="Converter e adicionar", height=42, command=_do).pack(padx=18, pady=(0, 18), fill="x")

    # ------------------- PRESENÇA -----------------------------------------------
    def build_presence(self):
        self.presence_view = ctk.CTkFrame(self.stage, fg_color="transparent")
        _, right, _ = self.page_header(self.presence_view, "eye", "DETECÇÃO DE PRESENÇA",
                                       "Checa processos vivos contra a base e suas strings personalizadas.")
        self.presence_btn = GlowButton(right, text="↻  Verificar agora", width=190, height=40, command=self._run_presence)
        self.presence_btn.pack(side="right")
        self.presence_scroll = ctk.CTkScrollableFrame(self.presence_view, fg_color=BG_PANEL, corner_radius=14,
                                                      border_width=1, border_color=BORDER_SOFT)
        self.presence_scroll.pack(fill="both", expand=True, padx=28, pady=(0, 18))
        ctk.CTkLabel(self.presence_scroll, text="Clique em “Verificar agora”.", font=(F_BODY, 13),
                     text_color=TEXT_DIM).pack(pady=50)

    def _run_presence(self):
        for w in self.presence_scroll.winfo_children():
            w.destroy()
        self.presence_btn.configure(state="disabled", text="Verificando…")
        ctk.CTkLabel(self.presence_scroll, text="Verificando processos…", font=(F_BODY, 13),
                     text_color=BLUE_NEON).pack(pady=30)
        threading.Thread(target=self._do_presence, daemon=True).start()

    def _do_presence(self):
        try:
            hits = scan_processes_for_strings(list(self.custom_strings))
        except Exception:
            hits = []
        self.ui(lambda: self._render_presence(hits))

    def _render_presence(self, hits):
        self.presence_btn.configure(state="normal", text="↻  Verificar agora")
        for w in self.presence_scroll.winfo_children():
            w.destroy()
        uniq = {}
        for h in hits:
            uniq[(h["pid"], h["label"])] = h
        hits = list(uniq.values())
        if not hits:
            box = ctk.CTkFrame(self.presence_scroll, fg_color="transparent")
            box.pack(pady=60)
            ctk.CTkLabel(box, text=self.ic("check"), font=self.icon_font(44), text_color=SEV_OK).pack()
            ctk.CTkLabel(box, text="Nenhum processo suspeito em execução agora.", font=(F_SEMI, 14),
                         text_color=SEV_OK).pack(pady=8)
            return
        ctk.CTkLabel(self.presence_scroll, text=f"{len(hits)} processo(s) suspeito(s) em execução", font=(F_HEAD, 15),
                     text_color=SEV_HIGH).pack(anchor="w", padx=14, pady=(12, 8))
        for h in sorted(hits, key=lambda x: SEV_RANK.get(x["severity"], 3)):
            col = SEV_COLORS.get(h["severity"], SEV_LOW)
            card = self.card(self.presence_scroll, radius=12)
            card.pack(fill="x", padx=10, pady=4)
            ctk.CTkFrame(card, fg_color=col, width=4, height=10, corner_radius=3).pack(side="left", fill="y", padx=(6, 0), pady=8)
            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(side="left", fill="both", expand=True, padx=12, pady=9)
            ctk.CTkLabel(inner, text=h["label"], font=(F_SEMI, 13), text_color=TEXT_MAIN).pack(side="left")
            ctk.CTkLabel(inner, text=f"PID {h['pid']} • {h['name']}", font=(F_MONO, 11), text_color=TEXT_DIM).pack(side="left", padx=10)
            self.sev_badge(inner, h["severity"]).pack(side="right")
            exe = ""
            try:
                exe = psutil.Process(h["pid"]).exe()
            except Exception:
                pass
            if exe:
                go, op, _, _ = self.file_actions(inner, exe)
                go.pack(side="right", padx=6)

    # ------------------- AJUSTES / SOBRE ----------------------------------------
    def build_settings(self):
        self.settings_view = ctk.CTkFrame(self.stage, fg_color="transparent")
        self.page_header(self.settings_view, "gear", "AJUSTES E SOBRE", "Base de assinaturas e informações do scanner.")
        wrap = self.card(self.settings_view, fg=BG_PANEL)
        wrap.pack(fill="both", expand=True, padx=28, pady=(0, 18))
        inner = ctk.CTkFrame(wrap, fg_color="transparent")
        inner.pack(padx=30, pady=26, fill="both", expand=True)
        ctk.CTkLabel(inner, text="Base de assinaturas", font=(F_HEAD, 16), text_color=TEXT_MAIN).pack(anchor="w")
        stats = ctk.CTkFrame(inner, fg_color="transparent")
        stats.pack(fill="x", pady=(10, 0))
        for i, (val, lbl) in enumerate([(len(CHEAT_CLIENTS), "clientes de xit"), (len(AUTOCLICKERS), "autoclickers e macros"),
                                        (len(BYPASS_TOOLS), "bypass / injeção"), (len(JAR_KEYWORDS), "palavras em bytecode"),
                                        (len(EXE_SIGNATURES), "assinaturas de EXE")]):
            stats.grid_columnconfigure(i, weight=1, uniform="st")
            c = self.card(stats)
            c.grid(row=0, column=i, sticky="nsew", padx=4)
            ctk.CTkLabel(c, text=str(val), font=(F_HEAD, 26), text_color=BLUE_NEON).pack(anchor="w", padx=14, pady=(10, 0))
            ctk.CTkLabel(c, text=lbl, font=(F_BODY, 12), text_color=TEXT_MUTED).pack(anchor="w", padx=14, pady=(0, 10))
            self._card_hover(c, self._descendants(c))
        ctk.CTkFrame(inner, fg_color=BORDER_SOFT, height=1).pack(fill="x", pady=22)
        ctk.CTkLabel(inner, text="Sobre", font=(F_HEAD, 16), text_color=TEXT_MAIN).pack(anchor="w")
        ctk.CTkLabel(inner, text=f"{APP_NAME} {VERSION} — Anti-Cheat System\n\n"
                                 "Envia um resumo da análise ao painel do time via Discord.\n"
                                 "Desenvolvido para screenshare em servidores de Minecraft.\n"
                                 "O scanner apenas LÊ e reporta — nunca apaga nada do jogador.\n\n"
                                 f"Strings personalizadas salvas em: {_custom_strings_path()}",
                     font=(F_BODY, 13), text_color=TEXT_MUTED, justify="left").pack(anchor="w", pady=(8, 18))
        GlowButton(inner, text="Entrar no Discord", width=220, height=42,
                   command=lambda: webbrowser.open(DISCORD_LINK)).pack(anchor="w")

    # ------------------- NAVEGAÇÃO ----------------------------------------------
    def show_view(self, key):
        for v in self._views.values():
            v.pack_forget()
        target = self._views.get(key, self.dash)
        target.pack(fill="both", expand=True)
        if key == "logs":
            self.filter_logs(self.current_category)
        elif key == "result":
            self.render_result()
        elif key == "strings":
            self.render_custom_strings()
        self._active_view = key
        self._set_nav_active(key)
        self._animate_view_in(target)

    def _animate_view_in(self, frame):
        steps = [18, 10, 5, 2, 0]

        def step(i=0):
            if not frame.winfo_ismapped() or i >= len(steps):
                return
            try:
                frame.pack_configure(pady=(steps[i], 0))
            except Exception:
                return
            self.after(16, lambda: step(i + 1))
        step()

    # ------------------- TICKERS ------------------------------------------------
    def tick_stats(self):
        try:
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent
            self.sb_sys.configure(text=f"CPU {cpu:.0f}%   RAM {ram:.0f}%   {datetime.now().strftime('%H:%M:%S')}")
        except Exception:
            pass
        self.after(1500, self.tick_stats)

    def _elapsed_str(self):
        if not self.scan_start:
            return "00:00"
        end = time.time() if self.scanning else (self.scan_end or time.time())
        sec = int(end - self.scan_start)
        h, rem = divmod(sec, 3600)
        m, s = divmod(rem, 60)
        return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

    def _has_critical(self):
        return self._crit_found

    def _cfg(self, w, **kw):
        """configure() só quando o valor muda (deixa a interface leve durante o scan)."""
        if getattr(w, "_cs_last", None) == kw:
            return
        w._cs_last = kw
        w.configure(**kw)

    def _ui_tick(self):
        """Atualiza o painel a partir do estado do scan (roda só na thread da interface)."""
        try:
            if self.main.winfo_ismapped() and self._active_view == "dash":
                target = 1.0 if self._scan_finished else self._progress
                diff = target - self._progress_shown
                if abs(diff) > 0.002:
                    self._progress_shown += diff * 0.25
                    self._draw_ring(self._progress_shown)
                self._spin = (self._spin + 1) % len(SPINNER)
                self._update_stages()
                self._cfg(self.time_lbl, text=self._elapsed_str())
                files = self.total_files
                det = self.total_detections
                self._cfg(self.files_lbl, text=f"{files:,}".replace(",", "."))
                self._cfg(self.det_num, text=str(det))
                self._cfg(self.clean_num, text=f"{max(0, files - len(self._flagged_paths)):,}".replace(",", "."))
                self._cfg(self.ring_sub, text=self._status_text[:60])
                self._update_recent()
            self._update_statusbar()
        except Exception:
            pass
        self.after(150, self._ui_tick)

    def _update_stages(self):
        for i, (ic, st) in enumerate(self.stage_rows):
            if self._scan_finished or i < self._stage:
                self._cfg(ic, text=self.ic("check"), font=self.icon_font(14), text_color=SEV_OK)
                self._cfg(st, text="Concluído", text_color=SEV_OK)
            elif i == self._stage and self.scanning:
                self._cfg(ic, text=SPINNER[self._spin], font=(F_SYMBOL, 15), text_color=BLUE_NEON)
                self._cfg(st, text="Em análise…", text_color=BLUE_NEON)
            else:
                self._cfg(ic, text=self.ic("clock"), font=self.icon_font(14), text_color=TEXT_DIM)
                self._cfg(st, text="Pendente", text_color=TEXT_DIM)

    def _update_recent(self):
        with self._lock:
            items = list(self._recent)
        sig = (len(items), self.total_detections)
        if sig == self._last_recent_sig:
            return
        self._last_recent_sig = sig
        items = list(reversed(items))
        if items:
            self.recent_empty.pack_forget()
        else:
            self.recent_empty.pack(pady=26)
        for i, (r, name, cat, path, sev, when) in enumerate(self.recent_rows):
            if i >= len(items):
                r.pack_forget()
                continue
            cat_name, it = items[i]
            p = it.get("path", "") or "—"
            name.configure(text=(it.get("name", "?")[:26]))
            cat.configure(text=cat_name)
            path.configure(text=p if len(p) <= 42 else "…" + p[-40:])
            s = it.get("severity", "LOW")
            bg, fg = SEV_BADGE.get(s, SEV_BADGE["LOW"])
            sev.configure(text=SEV_LABELS.get(s, s), fg_color=bg, text_color=fg)
            when.configure(text=f"Hoje {it.get('time', '')[:5]}")
            r._item = it
            r.pack(fill="x", padx=4, pady=1)

    def _update_statusbar(self):
        crit = self._has_critical()
        if self.scanning:
            self._cfg(self.sb_dot, text_color=BLUE_NEON)
            self._cfg(self.sb_text, text=f"Escaneamento em andamento…  {self._status_text[:70]}")
        elif self._scan_finished:
            self._cfg(self.sb_dot, text_color=SEV_OK if not self.total_detections else SEV_HIGH)
            self._cfg(self.sb_text, text=f"Verificação concluída em {self._elapsed_str()} — {self.total_detections} item(ns) encontrado(s)")
        if crit:
            self._cfg(self.sb_integrity, text="Comprometida", text_color=SEV_CRITICAL)
            self._cfg(self.sb_int_dot, text_color=SEV_CRITICAL)
        elif self.scanning:
            self._cfg(self.sb_integrity, text="Em análise", text_color=BLUE_NEON)
            self._cfg(self.sb_int_dot, text_color=BLUE_NEON)
        else:
            self._cfg(self.sb_integrity, text="Segura", text_color=SEV_OK)
            self._cfg(self.sb_int_dot, text_color=SEV_OK)

    # ------------------- SCAN CORE ----------------------------------------------
    def new_scan(self):
        self.show_view("dash")
        self.start_scan()

    def start_scan(self):
        if self.scanning:
            return
        self.scanning = True
        self._scan_finished = False
        self.scan_start = time.time()
        self.scan_end = 0
        with self._lock:
            self.logs_data = self._empty_logs()
            self._log_keys = set()
            self._flagged_paths = set()
            self._recent.clear()
        self.total_detections = 0
        self.total_files = 0
        self._progress = 0.0
        self._progress_shown = 0.0
        self._crit_found = False
        self._stage = 0
        self._last_recent_sig = None
        self._status_text = "Iniciando verificação…"
        self.start_btn.configure(state="disabled", text="ESCANEANDO…")
        self.scan_title.configure(text="ESCANEAMENTO EM ANDAMENTO")
        self.ring_hint.configure(text="Aguarde, isso pode levar alguns minutos.")
        self._draw_ring(0)
        self._scan_q = mp.Queue()
        self._scan_proc = mp.Process(target=scan_worker, args=(self._scan_q, list(self.custom_strings)))
        self._scan_proc.start()
        self.after(50, self._poll_scan)

    def add_log(self, category, item):
        """Registra um achado (chamado pela thread do scan). Junta repetidos."""
        key = (category, item.get("name"), item.get("path", ""))
        with self._lock:
            if key in self._log_keys:
                return
            self._log_keys.add(key)
            item.setdefault("time", datetime.now().strftime("%H:%M:%S"))
            self.logs_data[category].append(item)
            counts = category in DETECTION_CATEGORIES and item.get("severity") != "LOW"
            if counts:
                self.total_detections += 1
                if item.get("path"):
                    self._flagged_paths.add(item["path"])
                if item.get("severity") == "CRITICAL":
                    self._crit_found = True
            if category in DETECTION_CATEGORIES:
                self._recent.append((category, item))
        if counts and item.get("severity") == "CRITICAL" and time.time() - self._last_beep > 2:
            self._last_beep = time.time()
            try:
                if os.name == "nt":
                    import winsound
                    winsound.MessageBeep(0x00000030)
            except Exception:
                pass

    def update_progress(self, prog, text, stage=None):
        """Só guarda o estado; a interface lê isso em _ui_tick (sem tocar em widgets aqui)."""
        self._progress = min(prog, 0.99)
        self._status_text = text
        if stage is not None:
            self._stage = stage

    def _elevate(self):
        try:
            if try_elevate_admin():
                self.after(300, self._on_close)
        except Exception:
            pass

    def _poll_scan(self):
        """Lê a fila do processo de scan (na thread da interface, em pequenos lotes)."""
        q = self._scan_q
        if q is None:
            return
        finished = None
        t0 = time.time()
        try:
            while time.time() - t0 < 0.03:
                msg = q.get_nowait()
                kind = msg[0]
                if kind == "log":
                    self.add_log(msg[1], msg[2])
                elif kind == "progress":
                    self.update_progress(msg[1], msg[2], msg[3])
                elif kind == "files":
                    self.total_files = msg[1]
                elif kind in ("done", "error"):
                    finished = msg
                    break
        except queue.Empty:
            pass
        except Exception:
            pass
        if finished is None and self._scan_proc is not None and not self._scan_proc.is_alive() and q.empty():
            finished = ("error", "o processo de scan foi encerrado inesperadamente")
        if finished is None:
            self.after(80, self._poll_scan)
            return
        self._scan_q = None
        proc, self._scan_proc = self._scan_proc, None
        if proc is not None:
            threading.Thread(target=proc.join, args=(5,), daemon=True).start()
        if finished[0] == "error":
            self._finish_scan(error=finished[1])
        else:
            self._send_report()
            self._finish_scan()

    def _send_report(self):
        elapsed = int(time.time() - self.scan_start)
        all_detections = []
        by_category = {}
        with self._lock:
            for cat in DETECTION_CATEGORIES:
                items = [it for it in self.logs_data[cat] if it.get("severity") != "LOW"]
                all_detections.extend(items)
                by_category[cat] = len(items)
        _, _, _, _, top_reason = self._result_state()
        report = {"user": _safe_user(), "machine": platform.node(),
                  "os": f"{platform.system()} {platform.release()}", "scanned": self.total_files,
                  "elapsed": elapsed, "detections": all_detections,
                  "by_category": by_category, "top_reason": top_reason}
        threading.Thread(target=send_webhook, args=(report,), daemon=True).start()
        has_critical = any(d.get("severity") == "CRITICAL" for d in all_detections)
        if self.total_detections > 0:
            threading.Thread(target=play_alert_sound, args=(has_critical,), daemon=True).start()

    def _stop_scan_process(self):
        proc, self._scan_proc = self._scan_proc, None
        self._scan_q = None
        if proc is not None:
            try:
                for ch in psutil.Process(proc.pid).children(recursive=True):
                    ch.kill()
            except Exception:
                pass
            try:
                proc.terminate()
            except Exception:
                pass

    def _on_close(self):
        self._stop_scan_process()
        self.destroy()

    def _finish_scan(self, error=None):
        self.scanning = False
        self.scan_end = time.time()
        self._scan_finished = error is None
        self._progress = 1.0 if error is None else self._progress
        self.start_btn.configure(state="normal", text="↻  NOVA VERIFICAÇÃO")
        if error:
            self._status_text = f"Erro durante o scan: {error}"
            self.scan_title.configure(text="ESCANEAMENTO INTERROMPIDO")
            self.ring_hint.configure(text="Tente novamente como administrador.")
            return
        det = self.total_detections
        self._status_text = "Análise concluída — sistema limpo" if det == 0 else f"Análise concluída — {det} detecções"
        self.scan_title.configure(text="ESCANEAMENTO CONCLUÍDO")
        self.ring_hint.configure(text=f"Concluído em {self._elapsed_str()}.")
        self.risk_lbl.configure(text="STATUS: LIMPO" if det == 0 else f"STATUS: SUSPEITO ({det})",
                                text_color=SEV_OK if det == 0 else SEV_HIGH)
        self._draw_ring(1.0)
        self._progress_shown = 1.0
        self.after(400, lambda: self.show_view("result"))


# ==============================================================================
#                 ASSETS EMBUTIDOS (logo da onda + fundos do oceano)
# ==============================================================================
LOGO_B64 = "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"
OCEAN_B64 = "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fPrwWcPRxmsY6e/OvmOnNdXNTXO9jhcSaZ1lZrI1MjowOuAQMzUlk1lZYgQSlIIWXLryE1lYshBQiBUogEqAoCpQCixQKsFAStLMhalRQUsWiazU1JaA3JEqaKm7KROnMCWtdMbS9Oe7nSWy75jpyuTPPeM6dMdR0x0ubqLLMbN6zSc7gxjWZe3Tl1rljWTOsal6a59LG+fRO+p0sxm8yp1jxZ3ya3NQ6yEaxTteY1x7czljpia546ZmsJJda5w2zomN4XU1CYuZTWJalLc6sAkpcyyAljWCxF1kJKVLI3zBLFSyUCCUBAAlABZQCiyiylJRAKeqzzAihVAsqaQqoBVBE3m7M6LBEEW7x0s65luLvGrGs01cC4uISWaaza3059LnVySdOezpJCZkMZpe2saMY1gWbWbzpHTntPVePSzr5+nM1mQ58evGa3GY7XGrIzTqxs1nWTljeJcTSa457cZohbrNTXPUM2SaZ3kkslWCorSUSwFjMsWWSEpYsB0OebJUogWSyWywSyAVKIogAKlBbALZuzt93861z9nh9njVZZq9eNSWUFFiy2C2VLCllBCpUvTFstgQLFLuaubc6udyWy2UmsIvO5UF1c6Tes9LJEL059EtzKxEjCVewTPPWVm8ajeufSmuek775drHLpzNZzCcO/GUiXprluhk6b5dEqUxy68pZnRcc+nea8c6c5aRazRnvxIJZnWVTejnrMhYNELASwSyWSl1iwudQlRbkiLFSyEsUBLmWzOZemCXY1kCpRSwUbzbN5dbnlLFWDUAEoLpmy2UFSayKKAvTnpKWxLCyC6mrLvFubrOktzbNVgsQzLJoDdzU6osssTWs6q4uRm5jOkXpc1M51lZc1bvGkus2zt14bTWOmDM1TPDvwllxV3rnsGS756OmuW0nPplec1iXXNJrE1iaqUlgsDK5l1m6Oe8JZBag1INXJKlGbFglRCzUWazI1J0MSwktXK882JmbsWABsDWRQBZbBa36/Dq5l9PAyAC2BZQE1FreBKEUEspqUalspEsAo1VsusaubYsthLELGVQlqU1c7s0EXNN0sZujlm4lb57OkubM5smpc6Nb57stlTXTl0Ttz3mzOGJrpy6c452VprOkAmoN2Q3lkmNSXG885rfHVlzN81685ozqQZ1JZrJWswkuZaFITSCoAEJZKEaXMshZS5tMY3w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"
WHALE_B64 = "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"


if __name__ == "__main__":
    mp.freeze_support()
    app = CelestialScanner()
    app.mainloop()
