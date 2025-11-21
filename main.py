import flet as ft
import sqlite3
import threading
import time

def main(page: ft.Page):
    # --- CONFIGURAZIONE ---
    page.title = "Entropia OS - v0.9.4"
    page.theme_mode = "dark"
    page.padding = 10
    page.bgcolor = "#050505"
    page.window_width = 390
    page.window_height = 844

    # --- DATABASE ---
    conn = sqlite3.connect("database.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS particles (id INTEGER PRIMARY KEY AUTOINCREMENT, task_name TEXT, mass INTEGER, state TEXT)""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS lab_notes (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, content TEXT, category TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)""")
    try:
        cursor.execute("SELECT category FROM lab_notes LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE lab_notes ADD COLUMN category TEXT")
        conn.commit()
    conn.commit()

    # ==========================================
    # 1. GESTIONE ENTROPIA
    # ==========================================
    list_impact = ft.ListView(expand=True, spacing=10)
    list_flow = ft.ListView(expand=True, spacing=10)
    list_potential = ft.ListView(expand=True, spacing=10)
    
    new_task_input = ft.TextField(hint_text="Nuova particella...", expand=True, bgcolor="#1a1a1a", border_color="transparent", text_size=14)
    mass_slider = ft.Slider(min=1, max=10, divisions=9, value=5, label="{value}")
    state_selector = ft.Dropdown(
        width=120, options=[ft.dropdown.Option("Impatto"), ft.dropdown.Option("Flusso"), ft.dropdown.Option("Potenziale")],
        value="Flusso", bgcolor="#1a1a1a", text_size=12
    )

    def load_tasks():
        list_impact.controls.clear(); list_flow.controls.clear(); list_potential.controls.clear()
        cursor.execute("SELECT * FROM particles ORDER BY mass DESC")
        for row in cursor.fetchall():
            try:
                task_widget = render_task(row[0], row[1], row[2], row[3])
                if row[3] == "Impatto": list_impact.controls.append(task_widget)
                elif row[3] == "Potenziale": list_potential.controls.append(task_widget)
                else: list_flow.controls.append(task_widget)
            except: continue 
        page.update()

    def render_task(task_id, name, mass, state):
        colors = {"Impatto": "red", "Flusso": "cyan", "Potenziale": "purple"}
        accent = colors.get(state, "white")
        return ft.Container(
            content=ft.Row([
                ft.Icon(name="circle", color=accent, size=16),
                ft.Column([
                    ft.Text(name, size=14, weight="bold", color="white"),
                    ft.Text(f"m={mass}", size=10, color="grey")
                ], expand=True),
                ft.IconButton(icon="check_circle_outline", icon_color="#333333", icon_size=20, 
                              on_click=lambda e: delete_task(task_id))
            ]),
            bgcolor="#111111", padding=10, border_radius=8,
            border=ft.border.only(left=ft.border.BorderSide(2, accent))
        )

    def delete_task(task_id):
        cursor.execute("DELETE FROM particles WHERE id = ?", (task_id,))
        conn.commit()
        load_tasks()

    def add_task(e):
        if new_task_input.value:
            cursor.execute("INSERT INTO particles (task_name, mass, state) VALUES (?, ?, ?)", 
                           (new_task_input.value, int(mass_slider.value), state_selector.value))
            conn.commit()
            new_task_input.value = ""
            load_tasks()

    entropy_view = ft.Column([
        ft.Text("ENTROPIA", font_family="Courier New", weight="bold", color="grey"),
        ft.Row([new_task_input, ft.IconButton(icon="add", icon_color="cyan", on_click=add_task)]),
        ft.Row([state_selector, mass_slider], alignment="spaceBetween"),
        ft.Tabs(
            selected_index=1, animation_duration=300, expand=True, divider_color="transparent", indicator_color="cyan",
            tabs=[
                ft.Tab(text="Impatto", icon="flash_on", content=list_impact),
                ft.Tab(text="Flusso", icon="waves", content=list_flow),
                ft.Tab(text="Potenziale", icon="hourglass_bottom", content=list_potential),
            ]
        )
    ], expand=True)

    # ==========================================
    # 2. FOCUS (PERFECT CENTER FIX) ☢️
    # ==========================================
    timer_running = False
    input_min = ft.TextField(value="25", width=70, text_align="center", keyboard_type="number", label="MIN", border_color="#333")
    input_sec = ft.TextField(value="00", width=70, text_align="center", keyboard_type="number", label="SEC", border_color="#333")
    display_time = ft.Text("00:00", size=40, weight="bold", font_family="Courier New", color="cyan")
    
    reactor_ring = ft.ProgressRing(width=220, height=220, stroke_width=12, value=0, color="cyan", bgcolor="#111111")

    btn_timer = ft.ElevatedButton(
        content=ft.Text("INIZIALIZZA FOCUS", color="cyan"),
        bgcolor="#1a1a1a", width=200, 
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5))
    )

    def timer_loop(total_seconds):
        nonlocal timer_running
        current_s = total_seconds
        while current_s > 0 and timer_running:
            m, s = divmod(current_s, 60)
            display_time.value = f"{m:02d}:{s:02d}"
            reactor_ring.value = 1 - (current_s / total_seconds)
            page.update()
            time.sleep(1)
            current_s -= 1
        if timer_running:
            display_time.value = "DONE"
            reactor_ring.value = 1
            timer_running = False
            page.update()

    def toggle_timer(e):
        nonlocal timer_running
        if not timer_running:
            try:
                mins = int(input_min.value)
                secs = int(input_sec.value)
                tot = mins * 60 + secs
            except: return
            if tot > 0:
                timer_running = True
                input_min.disabled = True; input_sec.disabled = True
                btn_timer.content = ft.Text("ABORT", color="white")
                btn_timer.bgcolor = "red"
                reactor_ring.color = "cyan"
                threading.Thread(target=timer_loop, args=(tot,), daemon=True).start()
        else:
            timer_running = False
            input_min.disabled = False; input_sec.disabled = False
            btn_timer.content = ft.Text("INIZIALIZZA FOCUS", color="cyan")
            btn_timer.bgcolor = "#1a1a1a"
            display_time.value = "PAUSA"
            reactor_ring.value = 0
        page.update()

    btn_timer.on_click = toggle_timer

    focus_view = ft.Container(
        content=ft.Column([
            ft.Text("REAZIONE DI FOCUS", font_family="Courier New", size=18, weight="bold", color="grey"),
            ft.Divider(height=30, color="transparent"),
            ft.Row([input_min, ft.Text(":", size=30), input_sec], alignment="center"),
            ft.Divider(height=30, color="transparent"),
            
            # --- FIX ALLINEAMENTO ---
            ft.Stack([
                # Layer 1: Anello Esterno (Centrato nel contenitore 240x240)
                ft.Container(width=240, height=240, border=ft.border.all(1, "#222"), border_radius=120),
                
                # Layer 2: Anello Progresso (Centrato tramite alignment)
                ft.Container(
                    content=reactor_ring, 
                    alignment=ft.alignment.center, 
                    width=240, height=240
                ),
                
                # Layer 3: Nucleo (Centrato tramite alignment)
                ft.Container(
                    content=ft.Container(
                        content=display_time,
                        alignment=ft.alignment.center,
                        width=160, height=160, 
                        bgcolor="#0a0a0a", 
                        border_radius=80, 
                        border=ft.border.all(2, "#1a1a1a")
                    ),
                    alignment=ft.alignment.center,
                    width=240, height=240
                )
            ], width=240, height=240),
            # ------------------------

            ft.Divider(height=40, color="transparent"),
            btn_timer
        ], horizontal_alignment="center"),
        alignment=ft.alignment.center, expand=True
    )

    # ==========================================
    # 3. DIARIO 
    # ==========================================
    note_cat_input = ft.TextField(label="Materia", bgcolor="#1a1a1a", border_color="transparent", expand=1)
    note_title_input = ft.TextField(label="Titolo", bgcolor="#1a1a1a", border_color="transparent", expand=2)
    note_content_input = ft.TextField(hint_text="Dati ($$LaTeX$$)...", multiline=True, min_lines=3, bgcolor="#1a1a1a", border_color="transparent")
    notes_column = ft.Column(scroll="auto", expand=True)

    def delete_note(note_id):
        cursor.execute("DELETE FROM lab_notes WHERE id = ?", (note_id,))
        conn.commit()
        render_notes()

    def render_notes():
        notes_column.controls.clear()
        cursor.execute("SELECT DISTINCT category FROM lab_notes WHERE category IS NOT NULL ORDER BY category ASC")
        cats = [r[0] for r in cursor.fetchall()]
        cursor.execute("SELECT COUNT(*) FROM lab_notes WHERE category IS NULL")
        if cursor.fetchone()[0] > 0 and "Unsorted" not in cats: cats.append("Unsorted")

        if not cats:
            notes_column.controls.append(ft.Container(content=ft.Text("Nessun dato.", color="grey"), padding=20))
        
        for cat in cats:
            if cat == "Unsorted": query = "SELECT id, title, content FROM lab_notes WHERE category IS NULL ORDER BY id DESC"
            else: query = f"SELECT id, title, content FROM lab_notes WHERE category = '{cat}' ORDER BY id DESC"
            cursor.execute(query)
            cat_notes = []
            for row in cursor.fetchall():
                nid, ntitle, ncontent = row
                cat_notes.append(ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text(ntitle, weight="bold", color="cyan", expand=True),
                            ft.IconButton(icon="delete", icon_size=14, icon_color="#cf6679", on_click=lambda e, nid=nid: delete_note(nid))
                        ]),
                        ft.Markdown(ncontent, extension_set=ft.MarkdownExtensionSet.GITHUB_FLAVORED),
                    ]),
                    bgcolor="#111111", padding=10, border_radius=6, margin=ft.margin.only(bottom=5)
                ))
            notes_column.controls.append(ft.ExpansionTile(
                title=ft.Text(str(cat).upper(), weight="bold", color="white"),
                controls=cat_notes, initially_expanded=False, icon_color="cyan"
            ))
        page.update()

    def save_note(e):
        if note_title_input.value and note_content_input.value:
            cat = note_cat_input.value if note_cat_input.value else "Generale"
            cursor.execute("INSERT INTO lab_notes (title, content, category) VALUES (?, ?, ?)", 
                           (note_title_input.value, note_content_input.value, cat))
            conn.commit()
            note_title_input.value = ""; note_content_input.value = ""
            render_notes()

    lab_view = ft.Column([
        ft.Text("DIARIO", font_family="Courier New", weight="bold", color="grey"),
        ft.Row([note_cat_input, note_title_input]),
        note_content_input,
        ft.Container(content=ft.Text("REGISTRA DATI", color="black", weight="bold"), bgcolor="cyan", padding=10, border_radius=5, alignment=ft.alignment.center, on_click=save_note),
        ft.Divider(color="#222"),
        notes_column
    ], expand=True)

    # ==========================================
    # NAVIGAZIONE
    # ==========================================
    def change_tab(e):
        idx = e.control.selected_index
        if idx == 0: 
            load_tasks(); body.content = entropy_view
        elif idx == 1:
            body.content = focus_view
        elif idx == 2: 
            render_notes(); body.content = lab_view
        page.update()

    body = ft.Container(content=entropy_view, expand=True)
    nav_bar = ft.NavigationBar(
        destinations=[
            ft.NavigationBarDestination(icon="grid_view", label="Entropia"),
            ft.NavigationBarDestination(icon="api", label="Focus"), 
            ft.NavigationBarDestination(icon="book", label="Diario"),
        ],
        on_change=change_tab, bgcolor="#050505", indicator_color="#1a1a1a", surface_tint_color="#050505"
    )

    page.add(body, nav_bar)
    load_tasks()

ft.app(target=main)
