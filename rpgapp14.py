import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import json
import random
import os

# --- 1. データモデル層 ---
RANK_COLORS ={
            "S":"#FFD700",#gold
            "A":"#FF0000",#red
            "B":"#0000FF",#blue
            "C":"#00FFB7",#skyblue
            "D":"#90EE90",#lightgreen
            "E":"#FFA500",#orange
            "F":"#800080",#purple
            "G":"#000000"#black
        }
class Skill:
    def __init__(self, name, mp_cost, power, effect_type, duration=0):
        self.name = name
        self.mp_cost = mp_cost
        self.power = power
        self.effect_type = effect_type
        self.duration = duration

class Character:
    def __init__(self, name, job, hp, mp, atk, description, skills=None, image_path="images/chara.png",level=1,exp=0,rank=None, equipments=None,**kwargs):
        self.name = name
        self.job = job
        self.hp = hp
        self.max_hp = hp
        self.mp = mp
        self.max_mp = mp
        self.atk = atk
        self.description = description
        self.image_path = image_path if os.path.exists(image_path) else "images/chara.png"
        self.level = level
        self.exp = exp
        self.rank=rank
        # スキル文字列をオブジェクトに変換
        # 動的なステータス
        self.atk_modifier = 0  # 攻撃力の増減量
        self.buff_turns = 0    # バフの残りターン
        self.is_defending = False
        self.next_skill_index=0
        self.endefpower=0
        self.st_modifier=0
        self.st_turns=0
        
        self.raw_skills = skills if skills else []
        self.skills = []
        self.setup_skills()

        if equipments:
            self.equipments = equipments
        else:
            self.equipments = {"weapon1": None, "weapon2": None, "armor": None}
       
    @property
    def total_atk(self):
        """基本攻撃力 ＋ 装備のボーナスをリアルタイムに合計して返す"""
        bonus = 0
        if self.equipments["weapon1"]:
            bonus += self.equipments["weapon1"].get("atk_bonus", 0)
        if self.equipments["weapon2"]:
            bonus += self.equipments["weapon2"].get("atk_bonus", 0)
        return self.atk + bonus
    
    @property
    def total_hp(self):
        """基本HP ＋ 装備のボーナスをリアルタイムに合計して返す"""
        bonus = self.equipments["armor"]["hp_bonus"] if self.equipments["armor"] else 0
        return self.max_hp + bonus

    def setup_skills(self):
        """raw_skills の内容を整形して self.skills に格納する"""
        for s in self.raw_skills:
            # 名前から効果を推測する簡易ロジック
            if isinstance(s, dict):
                skill_data = {
                    "name": s.get("name",""),
                    "power": s.get("power", 1),
                    "mp_cost": s.get("mp_cost", 0),
                    "effect_type": s.get("effect_type", "damage")
                }
                if ("heal" in s.get("effect_type", "damage")) or ("defense" in s.get("effect_type", "damage")) or ("damage" in s.get("effect_type", "damage")):
                    self.skills.append(Skill(**skill_data))
                elif ("buff" in s.get("effect_type", "damage")) or ( "debuff"  in s.get("effect_type", "damage") or ("status" in s.get("effect_type", "damage"))):
                    self.skills.append(Skill(**skill_data, duration=3))
                

    @property

    def current_atk(self):
        """現在の攻撃力を計算（基本値 + 修正値）"""
        return max(1, self.atk + self.atk_modifier)

    def is_alive(self):
        return (self.hp + self.total_hp - self.max_hp) > 0

    def to_dict(self):
        """セーブ用に辞書形式へ変換"""
        return {
            "name": self.name, "job": self.job, "hp": self.hp,
            "mp": self.mp, "atk": self.atk,"level": self.level, 
            "exp": self.exp, "rank": self.rank,
            "description": self.description,
            "skills": self.raw_skills, "image_path": self.image_path,
            "equipments":self.equipments
        }
    
    def gain_exp(self, amount):
        """経験値を獲得し、レベルアップ判定を行う"""
        self.exp += amount
        leveled_up = False
        up_stats = {"hp": 0, "mp": 0, "atk": 0}
        
        # 次のレベルに必要な経験値 (例: レベル * 100)
        next_exp = self.level * 100
        
        while self.exp >= next_exp:
            self.level += 1
            self.exp -= next_exp
            leveled_up = True
            
            # ステータス上昇値の計算（ジョブごとに変えるのもアリ）
            h_up = random.randint(10, 20)
            m_up = random.randint(5, 10)
            a_up = random.randint(2, 5)
            
            self.max_hp += h_up
            self.hp = self.max_hp # レベルアップ時は全快
            self.max_mp += m_up
            self.mp = self.max_mp
            self.atk += a_up
            
            for skill in self.skills:
                skill.power += a_up

            up_stats["hp"] += h_up
            up_stats["mp"] += m_up
            up_stats["atk"] += a_up
            
            next_exp = self.level * 100 # 次のレベルへ
            
        return leveled_up, up_stats

    def calculate_rank(hp,atk):
        total_score=(hp/10)+atk
        if total_score<20:
            return "G"
        elif total_score<40:
            return "F"
        elif total_score<60:
            return "E"
        elif total_score<80:
            return "D"
        elif total_score<100:
            return "C"
        elif total_score<120:
            return "B"
        elif total_score<140:
            return "A"
        else:
            return "S"
        
    
    
    def generate_drop_item(hp,atk):
        """敵のレベルに応じた装備をランダム生成"""
        is_weapon = random.choice([True, False])
        item_type = random.choice(["weapon1","weapon2"]) if is_weapon else "armor"
        
        # ランク判定（ハクスラらしく！）
        rand = random.random()
        if rand > 0.95: rarity = "Legendary"; multiplier = 3.0
        elif rand > 0.8: rarity = "Rare"; multiplier = 1.5
        else: rarity = "Common"; multiplier = 1.0

        # 性能計算
        base_value = (hp/10+atk) * multiplier
        
        # アイテム名のプレフィックス（Geminiに生成させても面白い）
        prefixes = ["灼熱の","凍てつく","雷鳴の", "古びた", "聖なる", 
                    "風神の","大地の","呪われた","伝説の"]
        name_base = ["剣","弓","銃","ナイフ","斧"] if is_weapon else ["鎧","盾"]
        item_name = f"{random.choice(prefixes)}{random.choice(name_base)}"

        return {
            "name": item_name,
            "type": item_type,
            "atk_bonus": int(base_value) if is_weapon else 0,
            "hp_bonus": int(base_value) if not is_weapon else 0,
            "rarity": rarity
        }

# --- 2. 確認：詳細表示ウィンドウ ---
class DetailWindow(tk.Toplevel):
    def __init__(self, parent, character, side_color="#e0f0ff"):
        super().__init__(parent)
        self.title(f"データ照会: {character.name}")
        self.geometry("500x900")
        self.configure(bg=side_color)

        tk.Label(self, text=f"【{character.job}】", font=("Arial", 10)).pack(pady=5)
        tk.Label(self, text=character.name, font=("MS Gothic", 18, "bold"), bg=side_color).pack()
        
        # 画像表示
        self.canvas = tk.Canvas(self, width=300, height=300, bg="white", highlightthickness=0)
        self.canvas.pack(pady=10)
        try:
            img = Image.open(character.image_path).resize((300, 300))
            self.photo = ImageTk.PhotoImage(img)
            self.canvas.create_image(150, 150, image=self.photo)
        except:
            self.canvas.create_text(150, 150, text="No Image")

        # ステータス
        stats_frame = tk.Frame(self, bg="white", padx=10, pady=10)
        stats_frame.pack(fill="x", padx=20)
        tk.Label(stats_frame, text=f"HP: {character.hp}/{character.max_hp}", bg="white").pack(anchor="w")
        tk.Label(stats_frame, text=f"MP: {character.mp}/{character.max_mp}", bg="white").pack(anchor="w")
        tk.Label(stats_frame, text=f"ATK: {character.atk}", bg="white").pack(anchor="w")
        tk.Label(stats_frame, text=f"スキル: {', '.join([s.get('name', '') for s in character.raw_skills])}", bg="white", wraplength=300).pack(anchor="w", pady=5)
        tk.Label(stats_frame, text=f"レベル: {character.level}", bg="white").pack(anchor="w")
        target_color=RANK_COLORS.get(character.rank, "black")
        tk.Label(stats_frame, text=f"ランク: {character.rank}", fg=target_color,font=("Arial", 20,"bold")).pack(anchor="w")

        # 特徴
        tk.Label(self, text="― 特徴 ―", bg=side_color).pack(pady=5)
        tk.Label(self, text=character.description, wraplength=280, bg=side_color, justify="left").pack(padx=20)

        # --- 装備スロットセクション ---
        eq_frame = tk.LabelFrame(self, text="装備品", padx=10, pady=10)
        eq_frame.pack(fill="x", padx=20, pady=10)

        # 武器1
        self.create_equip_label(eq_frame, "武器1", character.equipments.get("weapon1"))
        # 武器2
        self.create_equip_label(eq_frame, "武器2", character.equipments.get("weapon2"))
        # 防具
        self.create_equip_label(eq_frame, "防具", character.equipments.get("armor"))
        
        tk.Button(self, text="閉じる", command=self.destroy).pack(pady=15)

    def create_equip_label(self, parent, slot_name, item):
        """スロット名とアイテム名を表示するラベルを作成"""
        row = tk.Frame(parent)
        row.pack(fill="x", pady=2)

        tk.Label(row, text=f"{slot_name}: ", font=("Arial", 10, "bold")).pack(side="left")

        if item:
            # アイテムがある場合 (名前を表示)
            # ランクがあれば色を変えるなどの工夫も可能
            item_name = item.get("name", "不明なアイテム")
            # レアリティに応じた色を取得（以前作った RANK_COLORS を流用）
            color = RANK_COLORS.get(item.get("rarity", "G"), "white")
            
            tk.Label(row, text=item_name, fg=color).pack(side="left")
            # ステータス上昇値も横に添えると親切
            bonus = f"(ATK +{item['atk_bonus']})" if item['type'] == "weapon" else f"(HP +{item['hp_bonus']})"
            tk.Label(row, text=f" {bonus}", fg="gray").pack(side="left")
        else:
            # アイテムがない場合
            tk.Label(row, text="なし", fg="gray").pack(side="left")

# --- 2. 戦闘：スキル選択GUIウィンドウ ---

class BattleWindow(tk.Toplevel):
    def __init__(self, app_instance, party, enemy_templates):
        super().__init__(app_instance.root)
        self.app = app_instance
        self.title("BATTLE: vs Multiple Enemies")
        self.geometry("1000x1100")
        
        style = ttk.Style()
        style.theme_use('default') # 'classic' や 'alt' でもOK

        # HPバーの色（緑）
        style.configure("HP.Horizontal.TProgressbar", foreground='green', background='green')
        # MPバーの色（青）
        style.configure("MP.Horizontal.TProgressbar", foreground='blue', background='blue')

        # 敵を実体化
        self.enemies = [Character(**e.to_dict()) for e in enemy_templates]
        self.party = party
        self.current_hero = self.party[0]
        self.pending_action = None  # 選択されたスキルを一時保存する用

        self.setup_battle_ui()
        self.update_ui()
        # 画像表示用のラベルを保持する辞書
        self.hero_flabels = {}
        self.enemy_flabels = {}

        # ビジュアル要素のセットアップ
        self.setup_visuals()

    def setup_visuals(self):
        # 画面上部に画像表示エリアを作成
        self.visual_frame = tk.Frame(self, bg="#2c3e50") # 背景色を少し暗くするとゲームらしい
        self.visual_frame.pack(fill="x", pady=30)

        # --- 味方エリア (左) ---
        self.ally_area = tk.Frame(self.visual_frame, bg="#2c3e50")
        self.ally_area.pack(side="left", expand=True)

        for hero in self.party:
            container = tk.Frame(self.ally_area, bg="#2c3e50")
            container.pack(side="top", pady=5)

            # 画像読み込み（職業.png を探す）
            try:
                full_path = f"images/{hero.job}.png"
                img = Image.open(full_path).convert("RGBA")
            except:
                img = Image.open(hero.image_path).convert("RGBA")

            img = img.resize((110, 110), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)

            lbl = tk.Label(container, image=photo, bg="#2c3e50")
            lbl.image = photo  # ガベージコレクション対策
            lbl.pack()
            
            self.hero_flabels[hero.name] = lbl
            tk.Label(container, text=hero.name, fg="white", bg="#2c3e50").pack()

        # --- 敵エリア (右) ---
        self.enemy_area = tk.Frame(self.visual_frame, bg="#2c3e50")
        self.enemy_area.pack(side="right", expand=True)

        for i, enemy in enumerate(self.enemies):
            container = tk.Frame(self.enemy_area, bg="#2c3e50")
            container.pack(side="top", pady=5) # 敵は縦に並べるとスッキリします

            try:
                img = Image.open(enemy.image_path).convert("RGBA")
            except:
                img = Image.open("images/default_enemy.png").convert("RGBA")

            img = img.resize((110, 110), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)

            lbl = tk.Label(container, image=photo, bg="#2c3e50")
            lbl.image = photo
            lbl.pack()
            
            # 敵は同じ名前が重なる可能性があるので、インスタンス自体をキーにするかIDを振る
            self.enemy_flabels[enemy.name] = lbl
            tk.Label(container, text=enemy.name, fg="white", bg="#2c3e50").pack()

    def setup_battle_ui(self):
        # --- 敵表示エリア（動的に作成） ---
        self.enemy_frame = tk.LabelFrame(self, text=" 敵軍団 ")
        self.enemy_frame.pack(pady=10, fill="x", padx=20)

        self.enemy_bars = []
        self.enemy_labels = []

        for i, en in enumerate(self.enemies):
            frame = tk.Frame(self.enemy_frame)
            frame.pack(fill="x", pady=10)
            lbl = tk.Label(frame, text=f"{en.name}", width=20)
            lbl.pack(side="left")
            bar = ttk.Progressbar(frame, length=200, maximum=en.max_hp)
            bar.pack(side="left", padx=20)
            bar["value"] = en.hp
            self.enemy_labels.append(lbl)
            self.enemy_bars.append(bar)
        self.refresh_enemy_display()
# プレイヤー情報
        self.hero_info = tk.Label(self, text="", font=("bold", 11))
        self.hero_info.pack()
        self.create_status_bars()
        self.refresh_bars()
        # ログエリア
        self.log_text = tk.Text(self, height=10, width=60, state='disabled', bg="#1a1a1a", fg="#00ff00")
        self.log_text.pack(pady=10)

        

        # コマンドエリア
        self.cmd_frame = tk.LabelFrame(self, text=" 行動を選択 ")
        self.cmd_frame.pack(pady=10, fill="x", padx=20)
        
        self.refresh_buttons()
        self.update_ui()

    def create_status_bars(self):
        self.hero_frame = tk.LabelFrame(self, text=" 味方 ")
        self.hero_frame.pack(pady=10, fill="x", padx=20)
        """キャラクターごとのステータス表示（名前 + HP/MPバー）を作成"""
        container = tk.Frame(self.hero_frame, padx=5, pady=5)
        container.pack(fill="x")
        
        self.bars = []
        for character in self.party:
            tk.Label(container, text=character.name, font=("Arial", 10, "bold")).pack(side="left")
            # --- HPバー ---
            # styleで色を変えるための設定（後述）
            hp_bar = ttk.Progressbar(container, orient="horizontal", length=150, mode="determinate",style="HP.Horizontal.TProgressbar")
            hp_bar.pack(side="left", padx=5)
            hp_bar["maximum"] = character.total_hp
            hp_bar["value"] = character.hp + character.total_hp - character.max_hp  # 装備のHPボーナスも反映させる

            # --- MPバー ---
            mp_bar = ttk.Progressbar(container, orient="horizontal", length=100, mode="determinate",style="MP.Horizontal.TProgressbar")
            mp_bar.pack(side="left", padx=5)
            mp_bar["maximum"] = character.max_mp
            mp_bar["value"] = character.mp

            # 後の更新のために保存しておく
            self.bars.append({"name": character.name, "hp": hp_bar, "mp": mp_bar})
        self.refresh_bars()    

    

    def add_log(self, msg):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')

    def update_ui(self):
        """戦闘画面の全情報を最新状態に更新する"""
        
        # 1. 味方（自分）の情報を更新
        hero = self.current_hero
        # バフ状態をアイコンで表現
        buff_icon = "🔥" if hero.atk_modifier > 0 else ""
        def_icon = "🛡️" if hero.is_defending else ""
        
        status_text = (
            f"[Lv.{hero.level}]  {hero.name}\n "
            f"(HP: {hero.hp+hero.total_hp-hero.max_hp}/{hero.total_hp}, MP: {hero.mp}/{hero.max_mp})\n "
            f"{hero.exp} exp 状態: {buff_icon}{def_icon} 正常"
        )
        self.hero_info.config(text=status_text)
        
        if hasattr(self.app, "update_after_battle"):
            self.app.update_after_battle()
        # 2. 敵軍団の情報（HPバーとラベル）を更新
        self.refresh_bars()
        self.refresh_enemy_display()

        # 3. 決着がついている場合はボタンを無効化するなどの制御
        if all(not e.is_alive() for e in self.enemies) or all(not h.is_alive() for h in self.party):
            for btn in self.cmd_frame.winfo_children():
                btn.config(state="disabled")
    def refresh_buttons(self):
        """キャラに合わせてスキルボタンを生成"""
        for w in self.cmd_frame.winfo_children(): w.destroy()
        normal_atk = Skill("通常攻撃", 0, self.current_hero.atk, "damage")
        tk.Button(self.cmd_frame, text="通常攻撃", command=lambda: self.prepare_action(normal_atk)).pack(side="left", padx=5)
        for s in self.current_hero.skills:
            # ターゲットが必要なスキル（攻撃・デバフ）だけを抽出
            if s.effect_type in ["damage", "debuff"]:
                btn = tk.Button(self.cmd_frame, text=f"{s.name} ({s.power}atk) ({s.mp_cost}MP)", 
                                command=lambda sk=s: self.prepare_action(sk))
                btn.pack(side="left", padx=5)
            elif s.effect_type in ["heal", "defense", "buff"]:
                # 回復は自分にかけるので即実行
                btn = tk.Button(self.cmd_frame, text=f"{s.name} ({s.power}atk) ({s.mp_cost}MP)", command=lambda sk=s: self.prepare_action(sk))
                btn.pack(side="left", padx=5)
        tk.Button(self.cmd_frame, text="交代", bg="#eee", command=self.open_switch).pack(side="right", padx=5)

    # --- ステップ1: 技を「予約」してターゲット選択へ ---
    def prepare_action(self, skill):
        if self.current_hero.mp < skill.mp_cost:
            messagebox.showwarning("MP不足", "MPが足りません！")
            return
        
        self.pending_action = skill
        
        # 効果タイプによって「敵を選ぶか」「味方を選ぶか」を分岐
        if skill.effect_type in ["damage", "debuff"]:
            self.show_enemy_target_selection()
        elif skill.effect_type in ["heal", "buff", "defense"]:
            self.show_ally_target_selection()

# --- ターゲット選択のフロー ---
    # --- ステップ2: ターゲットを選ばせる（サブウィンドウ） ---
    def show_enemy_target_selection(self):
        target_win = tk.Toplevel(self)
        target_win.title(f"{self.pending_action.name} の対象を選択")
        
        tk.Label(target_win, text="どの敵を狙いますか？").pack(pady=5)
        
        for en in self.enemies:
            if en.is_alive():
                btn = tk.Button(target_win, text=f"{en.name} (HP:{en.hp})", width=25,
                                command=lambda target=en, w=target_win: self.execute_pending_action(target, w))
                btn.pack(pady=2, padx=10)
    # --- ステップ2: 味方を選択させるウィンドウ ---
    def show_ally_target_selection(self):
        target_win = tk.Toplevel(self)
        target_win.title(f"{self.pending_action.name} の対象を選択")
        
        tk.Label(target_win, text="誰に使用しますか？").pack(pady=5, padx=20)
        
        # パーティーメンバー全員をボタンとして表示
        for member in self.party:
            # 戦闘不能のキャラにバフをかけられないようにする場合
            state = "normal" if member.is_alive() else "disabled"
            
            btn = tk.Button(target_win, text=f"{member.name} (HP:{member.hp})", 
                            width=25, state=state,
                            command=lambda m=member, w=target_win: self.execute_ally_action(m, w))
            btn.pack(pady=3, padx=10)
    # --- ステップ3: 技の実行 ---
    def execute_pending_action(self, target, window):
        window.destroy()  # 選択窓を閉じる
        skill = self.pending_action
        self.current_hero.mp -= skill.mp_cost

        atk_flabel=self.hero_flabels[self.current_hero.name]
        def_flabel =self.enemy_flabels[target.name]

        if skill.effect_type == "damage":
            if self.current_hero.level >= 10:
                self.add_log(f"⚡ {self.current_hero.name}の極まった魔力が炸裂！")
                self.animate_flash(atk_flabel,"yellow")
                for enemy in self.enemies:
                    def_flabel =self.enemy_flabels[enemy.name]
                    self.visual_frame.after(400, lambda: self.animate_flash(def_flabel,"red"))
                    if enemy.is_alive():
                        dmg = (skill.power+self.current_hero.total_atk-self.current_hero.atk) * 0.7 + self.current_hero.atk_modifier
                        if enemy.is_defending:
                            dmg -= enemy.endefpower
                            self.add_log(f"🛡 防御効果！ {enemy.name}はダメージを軽減した！")
                            enemy.is_defending = False # 一度受けたら解除
                        enemy.hp -= dmg
                        
                self.add_log(f"スキル「{skill['name']}」が敵を飲み込んだ！")
            else:
                self.animate_flash(atk_flabel,"yellow")
                self.visual_frame.after(400, lambda: self.animate_flash(def_flabel,"red"))
                dmg = skill.power+self.current_hero.total_atk-self.current_hero.atk + self.current_hero.atk_modifier
                if target.is_defending:
                    dmg -= target.endefpower
                    self.add_log(f"🛡 防御効果！ {target.name}はダメージを軽減した！")
                    target.is_defending = False # 一度受けたら解除
                target.hp -= dmg
            self.add_log(f"> {self.current_hero.name}の{skill.name}！ {target.name}に{dmg}のダメージ！")
        
        elif skill.effect_type == "debuff":
            if self.current_hero.level >= 10:
                self.add_log(f"⚡ {self.current_hero.name}の極まった魔力が炸裂！")
                self.animate_flash(atk_flabel,"yellow")
                

                for enemy in self.enemies:
                    def_flabel =self.enemy_flabels[enemy.name]
                    self.visual_frame.after(400, lambda: self.animate_flash(def_flabel,"purple"))
                    if enemy.is_alive():
                         enemy.atk_modifier += skill.power
                         enemy.buff_turns = skill.duration 
                self.add_log(f"スキル「{skill['name']}」が敵を弱体化させた！")
            else:
                self.animate_flash(atk_flabel,"yellow")
                self.visual_frame.after(400, lambda: self.animate_flash(def_flabel,"purple"))
                # デバフ処理（例：攻撃力を下げる）
                target.atk_modifier += skill.power
                target.buff_turns = skill.duration
                self.add_log(f"DOWN! {target.name}の攻撃力が下がった！")

        self.update_ui() # ダメージやデバフの結果をすぐに反映
        self.visual_frame.after(300, self.on_turn_end)
        self.pending_action = None # 予約クリア
        self.check_battle_status()
    def check_battle_status(self):
        self.update_ui()

        # 1. 勝利判定（すべての敵が死亡）
        if all(not e.is_alive() for e in self.enemies):
            self.add_log("★ 敵軍を殲滅しました！")
            self.show_victory_result()
            return True
        

        return False

    
    def enemies_turn(self):
        """生きている敵が順番に攻撃してくる"""
        for en in self.enemies:
            atk_flabel=self.enemy_flabels[en.name]
            def_flabel =self.hero_flabels[self.current_hero.name]
            if en.is_alive() and self.current_hero.is_alive():
                skill=en.skills[en.next_skill_index]
                en.next_skill_index =(en.next_skill_index + 1) % len(en.skills)
                if skill.effect_type == "damage":
                    dmg= skill.power - en.atk_modifier+self.current_hero.st_modifier
                else :
                    self.apply_enemy_effect(skill,en,atk_flabel)
                    for member in self.party:
                        if member.st_turns > 0:
                            dmg= member.st_modifier  
                            member.hp -= dmg
                            member.st_turns -= 1
                            self.add_log(f"<!> {en.name}の{skill.name}の効果！ {member.name}は{dmg}のダメージ！")
                        if member.st_turns == 0:
                            member.st_modifier = 0
                            
                    break
                # 防御判定
                if self.current_hero.is_defending:
                    dmg -= self.pending_action.power
                    self.add_log(f"🛡 防御効果！ ダメージを軽減した！")
                    self.current_hero.is_defending = False # 一度受けたら解除
                self.current_hero.hp -= dmg
                self.add_log(f"<!> {en.name}の攻撃！{skill.name} を放った！ {dmg}のダメージ！")
                self.animate_flash(atk_flabel,"yellow")
                self.visual_frame.after(400, lambda: self.animate_flash(def_flabel,"red"))
        
        self.visual_frame.after(300, self.update_ui)
        if not self.current_hero.is_alive():
            self.add_log(f"× {self.current_hero.name}は力尽きた...")

        if all(not p.is_alive() for p in self.party):
            self.show_defeat_result()
            return True
        
    def apply_enemy_effect(self,skill,en,atk_flabel):

        if skill.effect_type=="heal":
            heal_amt = skill.power
            en.hp = min(en.max_hp, en.hp + heal_amt)
            self.add_log(f"敵の{skill.name}！ {en.name}のHPが{heal_amt}回復！")
            self.animate_flash(atk_flabel,"yellow")
            self.visual_frame.after(400, lambda: self.animate_flash(atk_flabel,"green"))
        elif skill.effect_type=="defense":
            en.is_defending = True
            en.endefpower=skill.power
            self.add_log(f"敵の{skill.name}！ {en.name}は守りを固めた！")
            self.animate_flash(atk_flabel,"yellow")
            self.visual_frame.after(400, lambda: self.animate_flash(atk_flabel,"blue"))
        elif skill.effect_type=="status":
            def_flabel=self.hero_flabels[self.current_hero.name]
            self.current_hero.st_modifier += skill.power
            self.current_hero.st_turns = skill.duration
            self.add_log(f"敵の{skill.name}！ {self.current_hero.name}は状態異常に陥った！ {skill.power}のダメージ！")
            self.animate_flash(atk_flabel,"yellow")
            self.visual_frame.after(400, lambda: self.animate_flash(def_flabel,"purple"))


# --- ステップ3: 味方への実行処理 ---
    def execute_ally_action(self, target, window):
        window.destroy()
        skill = self.pending_action
        self.current_hero.mp -= skill.mp_cost


        atk_flabel=self.hero_flabels[self.current_hero.name]
        def_flabel =self.hero_flabels[target.name]
        
        if skill.effect_type == "heal":
            if self.current_hero.level >= 10:
                self.add_log(f"⚡ {self.current_hero.name}の極まった魔力が炸裂！")
                self.animate_flash(atk_flabel,"yellow")
                
                for member in self.party:
                    def_flabel =self.hero_flabels[member.name]
                    self.visual_frame.after(400, lambda: self.animate_flash(def_flabel,"green"))
                    if member.is_alive():
                        heal_amt = skill.power
                        member.hp = min(member.max_hp, member.hp + heal_amt)
                self.add_log(f"スキル「{skill['name']}」が味方全体を癒した！")
            else:
                self.animate_flash(atk_flabel,"yellow")
                self.visual_frame.after(400, lambda: self.animate_flash(def_flabel,"green"))
                heal_amt = skill.power
                target.hp = min(target.max_hp, target.hp + heal_amt)
                self.add_log(f"{self.current_hero.name}の{skill.name}！ {target.name}のHPが{heal_amt}回復！")

        elif skill.effect_type == "buff":
            if self.current_hero.level >= 10:
                self.add_log(f"⚡ {self.current_hero.name}の極まった魔力が炸裂！")
                self.animate_flash(atk_flabel,"yellow")
            
                for member in self.party:
                    def_flabel =self.hero_flabels[member.name]
                    self.visual_frame.after(400, lambda: self.animate_flash(def_flabel,"white"))
                    if member.is_alive():
                        member.atk_modifier += skill.power
                        member.buff_turns = skill.duration
                self.add_log(f"スキル「{skill['name']}」が味方全体を強化した！")
            else:
                self.animate_flash(atk_flabel,"yellow")
                self.visual_frame.after(400, lambda: self.animate_flash(def_flabel,"white"))
                target.atk_modifier += skill.power
                target.buff_turns = skill.duration
                self.add_log(f"🔥 {target.name}に{skill.name}！ 攻撃力が上がった！")

        elif skill.effect_type == "defense":
            if self.current_hero.level >= 10:
                self.add_log(f"⚡ {self.current_hero.name}の極まった魔力が炸裂！")
                self.animate_flash(atk_flabel,"yellow")
                for member in self.party:
                    def_flabel =self.hero_flabels[member.name]
                    self.visual_frame.after(400, lambda: self.animate_flash(def_flabel,"blue"))
                    if member.is_alive():
                        member.is_defending = True
                self.add_log(f"スキル「{skill['name']}」が味方全体を守り固めた！")
            else:
                self.animate_flash(atk_flabel,"yellow")
                self.visual_frame.after(400, lambda: self.animate_flash(def_flabel,"blue"))
                target.is_defending = True
                self.add_log(f"🛡 {target.name}は{skill.name}で守りを固めた！")

        self.pending_action = None
        self.update_ui()
        self.visual_frame.after(300, self.on_turn_end)
        
        

    def on_turn_end(self):
        """ターン終了時の状態更新処理"""
        
        # --- 1. 味方のバフ・防御状態の更新 ---
        hero = self.current_hero
        
        # 防御は1ターンで解除（敵の攻撃を受けた直後、または自分の行動終了時）
        if hero.is_defending:
            # ログに出すと煩雑な場合は、内部処理のみでOK
            hero.is_defending = False

        # バフのカウントダウン
        if hero.buff_turns > 0:
            hero.buff_turns -= 1
            if hero.buff_turns == 0:
                hero.atk_modifier = 0 # 攻撃力補正をリセット
                hero.st_modifier = 0 # ステータス補正をリセット
                self.add_log(f"🔔 {hero.name}の攻撃力アップ効果が終了した。")
            self.update_ui()
        # --- 2. 全ての敵のデバフ状態の更新 ---
        for en in self.enemies:
            if en.is_alive() and en.buff_turns > 0:
                en.buff_turns -= 1
                if en.buff_turns == 0:
                    en.atk_modifier = 0 # デバフ（攻撃力減少など）をリセット
                    self.add_log(f"✨ {en.name}の弱体化状態が回復した。")
                

        # UIの数値を最新状態にする
        self.update_ui()

        # --- 3. 次のフェーズへ ---
        # 敵がまだ生きているなら、敵のターンを開始
        if any(e.is_alive() for e in self.enemies):
            # 少し間を置いてから敵の攻撃を開始（演出用）
            self.after(800, self.enemies_turn)

    def refresh_bars(self):
        """全キャラクターの数値をバーに反映"""
        for en in self.party:
            for bar in self.bars:
                if bar["name"] == en.name:
                    # 1. HPバーの更新（最小0、最大値を下回らないように調整）
                    current_hp = max(0, en.hp+en.total_hp-en.max_hp)  # 装備のHPボーナスも反映させる
                    bar["hp"]["value"] = current_hp
                    bar["mp"]["value"] = en.mp
                  
        pass

    def refresh_enemy_display(self):
        """敵のHPバーとラベルを最新の状態に更新する"""
        for i, en in enumerate(self.enemies):
            # 1. HPバーの更新（最小0、最大値を下回らないように調整）
            current_hp = max(0, en.hp)
            self.enemy_bars[i]["value"] = current_hp
            
            # 2. ステータスラベルの更新
            if not en.is_alive():
                # 倒れている場合はグレーアウトして「撃破」と表示
                self.enemy_labels[i].config(
                    text=f"💀 {en.name} (撃破)", 
                    fg="#888888"
                )
            else:
                # 生きている場合は現在のHP数値を表示
                # バフ・デバフがかかっている場合にアイコンを出す演出もここで可能
                status_icons = ""
                if en.atk_modifier > 0: status_icons += " 🔺" # バフ
                if en.atk_modifier < 0: status_icons += " 🔻" # デバフ
                
                self.enemy_labels[i].config(
                    text=f"👾 {en.name} [HP: {current_hp}/{en.max_hp}]{status_icons}",
                    fg="black"
                )
        pass

    def show_victory_result(self):
        """勝利リザルト画面を表示し、経験値を分配する"""
        # 1. 獲得経験値の計算（例：敵の攻撃力の合計 × 10）
        total_exp = sum(en.atk for en in self.enemies) * 10
        
        # リザルト専用のサブウィンドウ
        result_win = tk.Toplevel(self)
        result_win.title("戦闘勝利")
        result_win.geometry("400x500")
        result_win.grab_set() # この画面を閉じるまで他を操作不能にする

        tk.Label(result_win, text="✨ VICTORY ✨", font=("MS Gothic", 20, "bold"), fg="#D4AF37").pack(pady=15)
        tk.Label(result_win, text=f"獲得経験値: {total_exp} EXP", font=("bold", 12)).pack(pady=5)

        # 2. 生存している味方に経験値を分配
        alive_members = [p for p in self.party if p.is_alive()]
        if not alive_members: return # 全滅時は呼ばれない想定だが念のため
        
        exp_per_person = total_exp // len(alive_members)

        for p in self.party:
            
            # 内部データ（Characterクラス）の経験値を増やし、レベルアップ判定
            leveled_up, up_stats = p.gain_exp( exp_per_person)
            
            self.app.update_after_battle()

            p.hp = p.max_hp # 戦闘後は全快させる（好みで調整可）
            p.mp = p.max_mp # 戦闘後は全快させる（好みで調整可）

            # 各キャラの結果を表示する枠
            char_frame = tk.Frame(result_win, relief="groove", bd=2, padx=10, pady=5)
            char_frame.pack(fill="x", padx=20, pady=5)
            
            # 名前と獲得EXP
            txt = f"{p.name} は {exp_per_person} EXP 獲得！"
            color = "black"
            
            if leveled_up:
                # レベルアップ時の強調表示
                txt += f" → Lv.{p.level} に上がった！"
                color = "blue"
                details = f"最大HP +{up_stats['hp']} / 最大MP +{up_stats['mp']} / 攻撃力 +{up_stats['atk']}"
                tk.Label(char_frame, text=details, fg="green", font=("small-caption", 9)).pack(side="bottom")
            
            tk.Label(char_frame, text=txt, fg=color, font=("bold", 10)).pack(side="top", anchor="w")

            for en in self.enemies:
                self.check_drops(en)
            p.rank=Character.calculate_rank(p.total_hp,p.total_atk)
            self.app.update_after_battle()

            
        # 3. 終了ボタン（ここから finish_battle を呼ぶ）
        tk.Button(result_win, text="キャンプへ戻る", font=("bold", 12),
                  bg="#4CAF50", fg="white", width=20,
                  command=self.finish_battle).pack(pady=20)

    def finish_battle(self):
        """戦闘結果（成長と消耗）を確定させ、メイン画面へ戻る"""


        # 1. 親ウィンドウ (GameApp) が存在するか確認
        if self.app:
            # 2. メイン画面の表示を更新 (update_after_battle を実行)
            # 戦闘中に Character オブジェクトの数値（HPやEXP）は既に書き換わっているため、
            # メイン画面の Listbox などを再描画するだけで最新状態になります。
            if hasattr(self.app, "update_after_battle"):
                self.app.update_after_battle()
                print("DEBUG: メイン画面のUIを更新しました。")
                for p in self.party:
                    print(f"DEBUG: {p.name} - LV:{p.level} EXP:{p.exp} ATK:{p.atk} HP:{p.max_hp}")
        # 3. データの永続化 (セーブ実行)
        # レベルアップしたステータスを即座にファイルに書き出します。
            if hasattr(self.app, "save_game"):
                self.app.save_game()
                print("DEBUG: 戦闘結果をセーブデータに保存しました。")

    # 4. 戦闘ウィンドウ（自分自身）を破棄
    # これにより Toplevel ウィンドウが消え、背後のメイン画面が操作可能になります。
        self.destroy()
    def show_defeat_result(self):
        """敗北画面の表示"""
        defeat_win = tk.Toplevel(self)
        defeat_win.title("GAME OVER")
        defeat_win.geometry("300x250")
        defeat_win.configure(bg="black")

        tk.Label(defeat_win, text="💀 TOTAL DEFEAT 💀", font=("bold", 18), fg="red", bg="black").pack(pady=20)
        tk.Label(defeat_win, text="パーティーは全滅した...", fg="white", bg="black").pack()

        for p in self.party:

            p.hp = p.max_hp # 戦闘後は全快させる（好みで調整可）
            p.mp = p.max_mp # 戦闘後は全快させる（好みで調整可）
        tk.Button(defeat_win, text="命からがら逃げ出す",command=self.destroy).pack(pady=20)
        
        
    def open_switch(self):
        sw = tk.Toplevel(self)
        for m in self.party:
            state = "normal" if m.is_alive() and m != self.current_hero else "disabled"
            tk.Button(sw, text=f"{m.name}(HP:{m.hp})", command=lambda char=m: self.switch_to(char, sw)).pack(pady=2)

    def switch_to(self, char, win):
        self.current_hero = char
        win.destroy()
        self.refresh_buttons()
        
        self.add_log(f"--- {char.name} が参戦！ ---")
        self.update_ui()
        
        self.after(600, self.enemies_turn)

    def animate_flash(self, label,color, count=0):
        """画像を3回白く点滅させる"""
        # 元の背景色を保持（初回のみ）
        if not hasattr(label, 'original_bg'):
            label.original_bg = label.cget("bg")
            
        if count < 6: # 3往復（白→元×3）
            new_bg = color if count % 2 == 0 else label.original_bg
            label.config(bg=new_bg)
            # 50ミリ秒後に次の点滅
            self.visual_frame.after(50, lambda: self.animate_flash(label, color, count + 1))
        else:
            # 最後に元の色に戻す
            label.config(bg=label.original_bg)

    def animate_shake(self, label, count=0):
        """画像を左右にガクガク揺らす"""
        # 親フレームのpadxを変更することで揺らす（Packを利用している場合）
        parent = label.master
        original_padx = parent.pack_info().get('padx', 0)
        
        if count < 8: # 4往復
            offset = 5 if count % 2 == 0 else -5
            parent.pack_configure(padx=original_padx + offset)
            # 30ミリ秒後に次の揺れ
            self.visual_frame.after(30, lambda: self.animate_shake(label, count + 1))
        else:
            # 最後に元の位置に戻す
            parent.pack_configure(padx=original_padx)
    
    def apply_damage_with_shake(self, def_flabel):
        self.animate_shake(def_flabel)

    def check_drops(self,en):
        if random.random() < 0.5:  # 50%でドロップ
            new_item = Character.generate_drop_item(en.hp,en.atk)

            self.add_log(f"💎 お宝発見！ {new_item['name']} ({new_item['rarity']}) を手に入れた！")
            
            # 簡易的な装備選択ダイアログを表示
            self.show_equipment_choice_ui(new_item)

    def show_equipment_choice_ui(self, new_item):
        """ドロップアイテムを誰に装備するか選ぶダイアログ"""
        dialog = tk.Toplevel(self)
        dialog.title("新アイテム獲得！")
        dialog.geometry("400x500")
        dialog.grab_set() # ダイアログを閉じるまで操作不可にする

        # --- 1. アイテム情報 ---
        rarity_color = RANK_COLORS.get(new_item['rarity'], "white") # ランクの色流用
        tk.Label(dialog, text="✨ NEW ITEM GET! ✨", font=("Arial", 12, "bold")).pack(pady=10)
        
        item_frame = tk.Frame(dialog, relief="ridge", bd=2, padx=10, pady=10)
        item_frame.pack(fill="x", padx=20)
        
        tk.Label(item_frame, text=new_item['name'], fg=rarity_color, font=("Arial", 16, "bold")).pack()
        stat_text = f"ATK +{new_item['atk_bonus']}" if new_item['type'] == "weapon1" or new_item['type']=="weapon2" else f"HP +{new_item['hp_bonus']}"
        tk.Label(item_frame, text=f"{new_item['rarity']} | {stat_text}").pack()

        tk.Label(dialog, text="誰に装備させますか？").pack(pady=10)

        # --- 2. キャラクター選択ループ ---
        for hero in self.party:
            hero_frame = tk.Frame(dialog, pady=5)
            hero_frame.pack(fill="x", padx=20)

            tk.Label(hero_frame, text=f"{hero.name}").pack(side="left")

            # 武器か防具かでボタンを出し分け
            if new_item['type'] == "weapon1":
                tk.Button(hero_frame, text="武器1", 
                        command=lambda h=hero: self.equip_item(h, "weapon1", new_item, dialog)).pack(side="right", padx=2)
            elif new_item['type']=="weapon2":
                tk.Button(hero_frame, text="武器2", 
                        command=lambda h=hero: self.equip_item(h, "weapon2", new_item, dialog)).pack(side="right", padx=2)
            else:
                tk.Button(hero_frame, text="防具へ", 
                        command=lambda h=hero: self.equip_item(h, "armor", new_item, dialog)).pack(side="right")

        tk.Button(dialog, text="捨てる", command=dialog.destroy).pack(pady=20)

    def equip_item(self, hero, slot, item, dialog):
        """実際に装備を適用し、ダイアログを閉じる"""
        # 装備適用
        hero.equipments[slot] = item
        

        # ログ出力
        self.add_log(f"✅ {hero.name}は {item['name']} を {slot} に装備した！")

        # UI更新（HPバーの最大値などが変わる可能性があるため）
        self.update_ui()
        
        # ダイアログを閉じる
        dialog.destroy()


# --- 3. メイン管理画面：セーブ＆ロード統合 ---

class GameApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Gemini RPG Editor Pro")
        self.root.geometry("850x700")
        self.save_file = "save_data.json"
        
        self.party = []
        self.enemies = []

        self.setup_ui()
        
        self.load_game() # 起動時に読み込み
        self.update_after_battle()

    def setup_ui(self):
        # JSON入力
        tk.Label(self.root, text="Gemini JSON Input", font=("bold", 10)).pack(pady=5)
        self.input_area = tk.Text(self.root, height=8, width=90)
        self.input_area.pack()

        # 登録ボタン
        btn_f = tk.Frame(self.root)
        btn_f.pack(pady=10)
        tk.Button(btn_f, text="味方登録", bg="#d0f0ff", command=lambda: self.register("player")).pack(side="left", padx=10)
        tk.Button(btn_f, text="敵登録", bg="#ffd0d0", command=lambda: self.register("enemy")).pack(side="left", padx=10)

        # リスト表示
        list_f = tk.Frame(self.root)
        list_f.pack(fill="both", expand=True, padx=20)
        
        # 味方側
        p_frame = tk.LabelFrame(list_f, text=" 味方パーティー (ダブルクリックで詳細) ")
        p_frame.pack(side="left", padx=20, fill="both", expand=True)
        self.p_list = tk.Listbox(p_frame,selectmode='multiple', exportselection=0)
        self.p_list.pack(fill="both", expand=True, padx=5, pady=5)
        self.p_list.bind('<Double-1>', lambda e: self.show_info("player"))

        # 敵側
        e_frame = tk.LabelFrame(list_f, text=" 出現モンスター (ダブルクリックで詳細) ")
        e_frame.pack(side="left", padx=20, fill="both", expand=True)
        self.e_list = tk.Listbox(e_frame,selectmode='multiple', exportselection=0)
        self.e_list.pack(fill="both", expand=True, padx=5, pady=5)
        self.e_list.bind('<Double-1>', lambda e: self.show_info("enemy"))
# ヘルプメッセージ
        tk.Label(self.root, text="※クリックで複数選択できます", fg="gray").pack()
        # 戦闘開始ボタン
        tk.Button(self.root, text="選んだ敵たちとバトル開始！", font=("bold", 14), 
                  bg="#ffcc99", command=self.start_multi_battle).pack(pady=20)
    
    def update_after_battle(self):
        """戦闘から戻ってきた時にメイン画面のパーティーリストを最新の状態にする"""
        
        # 1. リストボックスをクリア（古い情報を消去）
        self.p_list.delete(0, tk.END)
        
        # 2. 最新のパーティーデータをループで回して追加
        for char in self.party:
            # 生死状態のアイコン
            status_icon = "👤" if char.is_alive() else "💀"
            
            # 次のレベルまでの必要経験値を算出（Characterクラスの式に合わせる）
            next_exp_threshold = char.level * 100
            needed_exp = next_exp_threshold - char.exp
            
            # リストに表示する文字列の組み立て
            # 例: [ランクS][Lv.3] 👤 勇者アルス (HP: 120/120, MP: 45/45) Next: 25exp
            display_text = (
                f"[ランク{char.rank}][Lv.{char.level}] {status_icon} {char.name} "
                f"(HP: {char.hp}/{char.max_hp}, MP: {char.mp}/{char.max_mp}) "
                f"あと {needed_exp} exp"
            )
            self.p_list.insert(tk.END, display_text)
            r_color = RANK_COLORS.get(char.rank, "black")
            self.p_list.itemconfig(tk.END, fg=r_color)
            
            # 3. 視覚的なフィードバック（オプション）
            # HPが低いキャラを赤文字にするなどの工夫も可能（Listboxの仕様上、行ごとの色分けは工夫が必要）
            if not char.is_alive():
                self.p_list.itemconfig(tk.END, fg="black")

        print("システム: メイン画面のステータス表示を同期しました。")
    
    def save_game(self):
        print("--- DEBUG SAVE START ---")
        for hero in self.party:
            print(f"Name: {hero.name}, Hp: {hero.max_hp}, ATK: {hero.atk},EXP: {hero.exp}, LV: {hero.level}")
        print("--- DEBUG SAVE END ---")
        """現在の全キャラクターの状態（成長記録を含む）をJSONに保存"""
        try:
            # 1. 保存用データの組み立て
            save_data = {
                "party": [c.to_dict() for c in self.party],
                "enemies": [c.to_dict() for c in self.enemies]
            }

            # 2. ファイルへの書き出し
            with open(self.save_file, "w", encoding="utf-8") as f:
                # indent=4 で人間が読める形式に、ensure_ascii=False で日本語をそのまま保存
                json.dump(save_data, f, indent=4, ensure_ascii=False)
            
            print("セーブ完了: レベルと経験値が保存されました。")
            
        except Exception as e:
            messagebox.showerror("セーブ失敗", f"データの保存中にエラーが発生しました:\n{e}")

    def load_game(self):
        """保存されたJSONからデータを読み込み、オブジェクトとして復元する"""
        if not os.path.exists(self.save_file):
            print("セーブデータが見つかりません。新規作成します。")
            return

        try:
            with open(self.save_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 1. 味方パーティーの復元
            self.party = []
            for d in data.get("party", []):
                # 辞書の中身を Character クラスの引数に展開 (**d)
                char = Character(
                        name=d["name"],
                        job=d["job"],
                        hp=d["hp"],
                        mp=d["mp"],
                        atk=d["atk"],
                        description=d["description"],
                        image_path=d["image_path"],
                        skills=d.get("skills", []),
                        level=d.get("level", 1),
                        exp=d.get("exp", 0),
                        rank=d.get("rank", "G"),          # ← ランクを渡す
                        equipments=d.get("equipments",[])    # ← 装備データを渡す
                    )
                self.party.append(char)

                

            # 2. 敵リスト（図鑑）の復元
            self.enemies = []
            for d in data.get("enemies", []):
                char = Character(**d)
                self.enemies.append(char)
                display=(f"[ランク{char.rank}]{char.name}")
                self.e_list.insert(tk.END, display)
                r_color = RANK_COLORS.get(char.rank, "white")
                self.e_list.itemconfig(tk.END, fg=r_color)

            # 3. 画面表示の更新
            self.update_after_battle() 
            print(f"ロード完了: {len(self.party)}人の仲間を読み込みました。")

        except Exception as e:
            messagebox.showerror("ロード失敗", f"データの読み込み中にエラーが発生しました:\n{e}")

    def register(self, side):
        try:
            data = json.loads(self.input_area.get("1.0", tk.END))
            skills_list=[]

            if isinstance(data.get("skills", []), str):
                skills_list = json.loads(data.get("skills", []))
            else:
                skills_list = data.get("skills", [])

            equipments_list=[]

            if isinstance(data.get("equipments", []), str):
                equipments_list = json.loads(data.get("equipments", []))
            else:
                equipments_list = data.get("equipments", [])

            rank = Character.calculate_rank(data["hp"], data["atk"])

            char = Character(
                name=data["name"],
                job=data["job"],
                hp=data["hp"],
                mp=data["mp"],
                atk=data["atk"],
                description=data["description"],
                image_path=data["image_path"],
                skills=skills_list,  # ここで整形済みのリストを渡す！
                level=1,
                exp=0,
                rank=rank,
                equipments=equipments_list
            )
            if side == "player":
                self.party.append(char)
                self.save_game() # 登録のたびにセーブ
                self.update_after_battle()
            else:
                self.enemies.append(char)
                self.e_list.insert(tk.END, char.name)
                self.save_game() # 登録のたびにセーブ
        
            self.input_area.delete("1.0", tk.END)
        except Exception as e: messagebox.showerror("Error", e)
    def show_info(self, side):
        if side == "player":
            idx = self.p_list.curselection()
            if idx: DetailWindow(self.root, self.party[idx[0]], "#e0f0ff")
        else:
            idx = self.e_list.curselection()
            if idx: DetailWindow(self.root, self.enemies[idx[0]], "#ffe0e0")

    def start_multi_battle(self):
        p_idx = self.p_list.curselection()
        e_idx = self.e_list.curselection()
        if not p_idx:
            return messagebox.showwarning("警告", "味方を登録してください")
        if not e_idx:
            return messagebox.showwarning("警告", "戦う敵を1体以上選んでください")

        # 選択された敵のデータをリストにまとめる
        selected_hero = [self.party[i] for i in p_idx]  # 最初の選択を出撃キャラにする
        selected_enemies = [self.enemies[i] for i in e_idx]

        # 戦闘ウィンドウにリストを渡す
        BattleWindow(self, selected_hero, selected_enemies)

        


if __name__ == "__main__":
    GameApp().root.mainloop()