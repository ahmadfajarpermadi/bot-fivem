import discord
import requests
from discord.ext import commands
from server_manager import get_players_cfx, load_servers, save_servers
from dotenv import load_dotenv
import os

import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Bot is alive')

def run_web():
    server = HTTPServer(('0.0.0.0', 8080), Handler)
    server.serve_forever()

threading.Thread(target=run_web, daemon=True).start()

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(
    command_prefix="=",
    intents=intents,
    help_command=None  # 🔥 disable default help
)

servers = load_servers()


# ========================
# UTIL
# ========================
def get_ping_emoji(ping):
    if ping < 50:
        return "🟢"
    elif ping < 100:
        return "🟡"
    return "🔴"


def format_player(p):
    ping = p.get("ping", 0)
    emoji = get_ping_emoji(ping)
    return f"{emoji} **[{p['id']}]** {p['name']} • `{ping}ms`"

def extract_join_code(input_str):
    if "cfx.re/join/" in input_str:
        return input_str.split("cfx.re/join/")[-1]
    return input_str

def create_progress_bar(current, max_value, length=20):
    ratio = current / max_value if max_value else 0
    filled = int(ratio * length)
    empty = length - filled
    return "█" * filled + "░" * empty

def create_server_embed(info, keyword=None):
    title = f"🔎 {info['hostname']}"
    if keyword:
        title += f" — Mencari: {keyword}"

    embed = discord.Embed(
        title=title,
        description=(
            f"🖥️ {info['hostname']}\n"
            f"👥 {info['clients']}/{info['sv_maxclients']} Pemain Online"
        ),
        color=discord.Color.from_rgb(110, 0, 0)
    )

    # 🔥 FIX DI SINI
    banner = info.get("vars", {}).get("banner_detail")

    if isinstance(banner, str):
        banner = banner.replace("i.ibb.co.com", "i.ibb.co")

    if banner and banner.startswith("http"):
        embed.set_image(url=banner)

    embed.set_footer(text="⚡ FiveM Info Player • by TELO GAMING 😈")

    return embed
# ========================
# PAGINATION VIEW
# ========================
class PlayerView(discord.ui.View):
    def __init__(self, players, info):
        super().__init__(timeout=90)
        self.players = players
        self.info = info
        self.page = 0
        self.per_page = 22

    def get_max_page(self):
        return (len(self.players) - 1) // self.per_page

    def update_buttons(self):
        self.prev.disabled = self.page == 0
        self.next.disabled = self.page >= self.get_max_page()

    def get_embed(self):
        total = len(self.players)
        max_page = self.get_max_page()

        start = self.page * self.per_page
        end = start + self.per_page
        chunk = self.players[start:end]

        # 🎯 Progress Bar
        progress = create_progress_bar(self.info['clients'], self.info['sv_maxclients'])

        embed = discord.Embed(
            title=f"🌐 {self.info['hostname']}",
            description=(
                f"👥 **{self.info['clients']}/{self.info['sv_maxclients']} Player Online**\n"
                f"`{progress}`\n"
                f"📄 Halaman {self.page+1}/{max_page+1}"
            ),
            color=discord.Color.from_rgb(110, 0, 0)
        )
        banner = self.info.get("banner_detail")

        if isinstance(banner, str):
            banner = banner.replace("i.ibb.co.com", "i.ibb.co")

        if banner and banner.startswith("http"):
            embed.set_image(url=banner)
        # 📋 Player List
        text = "\n".join([format_player(p) for p in chunk])

        embed.add_field(
            name="📋 Daftar Player",
            value=text if text else "Tidak ada player",
            inline=False
        )
        self.update_buttons()
        return embed

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.secondary)
    async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 0:
            self.page -= 1
        await interaction.response.edit_message(embed=self.get_embed(), view=self)


    @discord.ui.button(label="➡️", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page < self.get_max_page():
            self.page += 1
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

class SearchView(discord.ui.View):
    def __init__(self, results, keyword, info):
        super().__init__(timeout=90)
        self.results = results
        self.keyword = keyword
        self.info = info
        self.page = 0
        self.per_page = 22

        if len(results) <= self.per_page:
            self.clear_items()

    def get_max_page(self):
        return (len(self.results) - 1) // self.per_page

    def update_buttons(self):
        self.prev.disabled = self.page == 0
        self.next.disabled = self.page >= self.get_max_page()

    def get_embed(self):
        total = len(self.results)
        max_page = self.get_max_page()

        start = self.page * self.per_page
        end = start + self.per_page
        chunk = self.results[start:end]

        embed = discord.Embed(
            title=f"👥 Pemain {start+1}-{min(end, total)}",
            description=f"👥 Jumlah Player: **{total}**",
            color=discord.Color.from_rgb(110, 0, 0)
        )

        text = "\n".join([format_player(p) for p in chunk])

        embed.add_field(
            name="📋 Daftar Player",
            value=text if text else "Tidak ada hasil",
            inline=False
        )

        embed.set_footer(text=f"📄 Halaman {self.page+1}/{max_page+1}")

        self.update_buttons()
        return embed
    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.secondary)
    async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 0:
            self.page -= 1
        await interaction.response.edit_message(embed=self.get_embed(), view=self)


    @discord.ui.button(label="➡️", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page < self.get_max_page():
            self.page += 1
        await interaction.response.edit_message(embed=self.get_embed(), view=self)
# ========================
# SERVER LIST
# ========================
@bot.command()
async def serverlist(ctx):
    embed = discord.Embed(
        title="🌐 Server List",
        description="Gunakan `=allplayer <id>` untuk melihat player",
        color=discord.Color.from_rgb(110, 0, 0)
    )

    for key, s in servers.items():
        embed.add_field(
            name=f"🆔 {key}",
            value=f"📛 {s['name']}",
            inline=False
        )

    await ctx.send(embed=embed)


# ========================
# ALL PLAYER (PAGINATION)
# ========================
@bot.command()
async def allplayer(ctx, server_id):
    if server_id not in servers:
        await ctx.send("❌ Server tidak ditemukan.")
        return

    players, info = get_players_cfx(servers[server_id]["join_code"])
    if not players:
        await ctx.send("⚠️ Tidak bisa mengambil data server.")
        return

    server_embed = create_server_embed(info)
    view = PlayerView(players, info)

    await ctx.send(embed=server_embed)
    await ctx.send(embed=view.get_embed(), view=view)
# ========================
# SEARCH PLAYER
# ========================
@bot.command()
async def player(ctx, server_id, *, nama):
    if server_id not in servers:
        await ctx.send("❌ Server tidak ditemukan.")
        return

    players, info = get_players_cfx(servers[server_id]["join_code"])
    if not players:
        await ctx.send("⚠️ Tidak bisa mengambil data.")
        return

    hasil = [p for p in players if nama.lower() in p["name"].lower()]

    if not hasil:
        await ctx.send("❌ Player tidak ditemukan.")
        return

    # 🔥 EMBED 1 (SERVER INFO)
    server_embed = create_server_embed(info, nama)

    # 🔥 EMBED 2 (PLAYER LIST)
    view = SearchView(hasil, nama, info)
    player_embed = view.get_embed()

    await ctx.send(embed=server_embed)
    await ctx.send(embed=player_embed, view=view)
# ========================
# ADD SERVER
# ========================
@bot.command()
async def addserver(ctx, server_id, *, link):
    global servers

    if server_id in servers:
        await ctx.send("❌ ID server sudah ada.")
        return

    join_code = extract_join_code(link)

    # validasi sederhana (optional tapi bagus)
    players, info = get_players_cfx(join_code)

    if not info:
        await ctx.send("❌ Server tidak valid / tidak bisa diakses.")
        return

    servers[server_id] = {
        "name": info["hostname"],
        "join_code": join_code
    }

    save_servers(servers)

    embed = discord.Embed(
        title="✅ Server Berhasil Ditambahkan",
        description=f"🆔 {server_id}\n📛 {info['hostname']}",
        color=discord.Color.from_rgb(110, 0, 0)
    )

    await ctx.send(embed=embed)
# ========================
# ADD SERVER
# ========================
@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title="🤖 Bantuan Bot FiveM",
        description="Daftar command yang tersedia:",
        color=discord.Color.from_rgb(110, 0, 0)
    )

    # 📊 SERVER
    embed.add_field(
        name="🌐 Server",
        value=(
            "`=serverlist`\n"
            "→ Menampilkan daftar server\n"
        ),
        inline=False
    )

    # 🎮 PLAYER
    embed.add_field(
        name="🎮 Player",
        value=(
            "`=allplayer <id server>`\n"
            "→ Lihat semua player\n\n"
            "`=player <id server> <nama>`\n"
            "→ Cari player berdasarkan nama"
        ),
        inline=False
    )

    # ⚙️ ADMIN
    embed.add_field(
        name="⚙️ Manajemen Server",
        value=(
            "`=addserver <id server> <join code>`\n"
            "→ Tambah server baru\n"
        ),
        inline=False
    )

    # 💡 CONTOH
    embed.add_field(
        name="💡 Contoh",
        value=(
            "`=allplayer ime`\n"
            "`=player ime lotf`\n"
            "`=addserver ime zrvmg4`\n"
        ),
        inline=False
    )

    # 🔑 JOIN CODE GUIDE
    embed.add_field(
        name="🔑 Apa itu Join Code?",
        value=(
            "Join code adalah kode unik server FiveM.\n\n"
            "📌 Contoh link:\n"
            "`https://cfx.re/join/zrvmg4`\n\n"
            "👉 Join code adalah bagian akhir:\n"
            "`zrvmg4`\n\n"
            "Gunakan saat menambahkan server:\n"
            "`=addserver ime zrvmg4`"
        ),
        inline=False
    )

    # 🌐 CONTOH NYATA
    embed.add_field(
        name="🌍 Contoh Server Nyata",
        value=(
            "**iMe RP**\n"
            "`cfx.re/join/zrvmg4`"
        ),
        inline=False
    )

    # 🖼️ GAMBAR (GANTI LINK SESUAI GAMBAR KAMU)
    embed.set_image(
        url="https://raw.githubusercontent.com/ahmadfajarpermadi/bot-fivem/master/addserver.png"  # 🔥 ganti dengan gambar yang kamu upload
    )

    embed.set_footer(text="⚡ FiveM Discord Bot • Made by TELO GAMING 😈")

    await ctx.send(embed=embed)
bot.run(TOKEN)
