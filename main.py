
import os
import tkinter as tk
from tkinter import ttk, messagebox
import requests
import threading


API_KEY = os.environ.get("uvff13ukrn6fik0i5avzzeladf5q0oi6kj3hpm2o", "").strip() or "BURAYA_GEÇERLİ_KEYİNİ_YAZ"
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

class WeatherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Hava Durumu")
        self.geometry("480x300")
        self.resizable(False, False)

        style = ttk.Style(self)
        style.theme_use("clam")

        self._build_ui()

    def _build_ui(self):
        container = ttk.Frame(self, padding=16)
        container.pack(fill="both", expand=True)

        top = ttk.Frame(container)
        top.pack(fill="x")

        ttk.Label(top, text="Şehir:", font=("Segoe UI", 10)).pack(side="left")
        self.city_var = tk.StringVar(value="İstanbul")
        self.entry = ttk.Entry(top, textvariable=self.city_var, width=30)
        self.entry.pack(side="left", padx=8)
        # DÜZELTME: HTML kaçışlı metin yerine gerçek <Return>
        self.entry.bind("<Return>", lambda e: self.fetch_weather())

        self.btn = ttk.Button(top, text="Getir", command=self.fetch_weather)
        self.btn.pack(side="left")

        self.result = tk.StringVar(value="Hazır.")
        self.result_label = ttk.Label(container, textvariable=self.result, font=("Segoe UI", 11), justify="left")
        self.result_label.pack(anchor="w", pady=(14,4))

        self.status = tk.StringVar(value="Durum: Beklemede")
        ttk.Label(container, textvariable=self.status, foreground="#555").pack(anchor="w")

        self.icon_label = ttk.Label(container, text="⛅", font=("Segoe UI Emoji", 28))
        self.icon_label.pack(anchor="center", pady=6)

    def fetch_weather(self):
        if not API_KEY or len(API_KEY) < 20:
            messagebox.showerror("Hata", "API anahtarı tanımlı değil veya geçersiz. Lütfen OWM_API_KEY'i ayarlayın ya da kodda geçerli bir anahtar kullanın.")
            return

        city = self.city_var.get().strip()
        if not city:
            messagebox.showwarning("Uyarı", "Lütfen bir şehir adı girin.")
            return

        self.btn.config(state="disabled")
        self.status.set("Durum: Veriler alınıyor...")
        self.result.set("")

        thread = threading.Thread(target=self._request_weather, args=(city,), daemon=True)
        thread.start()

    def _request_weather(self, city):
        params = {"q": city, "appid": API_KEY, "units": "metric", "lang": "tr"}
        try:
            resp = requests.get(BASE_URL, params=params, timeout=12)

            # 401 özel kontrol: Kullanıcıya daha anlaşılır mesaj
            if resp.status_code == 401:
                try:
                    msg = resp.json().get("message", "Yetkisiz erişim (401). API anahtarınızı kontrol edin.")
                except Exception:
                    msg = "Yetkisiz erişim (401). API anahtarınızı kontrol edin."
                self.after(0, lambda m=msg: self._on_error(m))
                return

            resp.raise_for_status()
            data = resp.json()

            if data.get("cod") != 200:
                # Örn: {"cod":"404","message":"city not found"}
                msg = data.get("message", "Bilinmeyen hata")
                self.after(0, lambda m=msg: self._on_error(m))
                return

            name = data["name"]
            country = data["sys"]["country"]
            temp = data["main"]["temp"]
            feels = data["main"]["feels_like"]
            humidity = data["main"]["humidity"]
            wind = data["wind"]["speed"]
            desc = data["weather"][0]["description"].capitalize()
            icon_code = data["weather"][0]["icon"]

            text = (
                f"{name}, {country}\n"
                f"Durum: {desc}\n"
                f"Sıcaklık: {temp:.1f} °C (Hissedilen: {feels:.1f} °C)\n"
                f"Nem: %{humidity}\n"
                f"Rüzgâr: {wind} m/s"
            )

            self.after(0, lambda txt=text, code=icon_code: self._on_success(txt, code))

        except requests.exceptions.Timeout:
            self.after(0, lambda msg="İstek zaman aşımına uğradı.": self._on_error(msg))
        except requests.exceptions.HTTPError as exc:
            self.after(0, lambda msg=f"HTTP Hatası: {exc}": self._on_error(msg))
        except Exception as exc:
            self.after(0, lambda msg=f"Hata: {exc}": self._on_error(msg))

    def _on_success(self, text, icon_code):
        self.result.set(text)
        self.status.set("Durum: Tamamlandı")
        self.btn.config(state="normal")
        emoji = self._icon_from_code(icon_code)
        self.icon_label.config(text=emoji)

    def _on_error(self, msg):
        self.status.set("Durum: Hata")
        self.btn.config(state="normal")
        messagebox.showerror("Hata", msg)

    @staticmethod
    def _icon_from_code(code: str) -> str:  # DÜZELTME: -> str
        if code.startswith("01"):
            return "☀️"
        if code.startswith("02"):
            return "🌤️"
        if code.startswith("03") or code.startswith("04"):
            return "☁️"
        if code.startswith("09") or code.startswith("10"):
            return "🌧️"
        if code.startswith("11"):
            return "⛈️"
        if code.startswith("13"):
            return "❄️"
        if code.startswith("50"):
            return "🌫️"
        return "⛅"

if __name__ == "__main__":
    app = WeatherApp()
    app.mainloop()
