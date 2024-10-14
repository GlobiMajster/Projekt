from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
import requests  # Do komunikacji z urządzeniami za pomocą HTTP
from zeroconf import ServiceBrowser, Zeroconf, ServiceStateChange


class SmartHomeApp(App):
    def build(self):
        self.device_list = []  # Lista wykrytych urządzeń
        self.room_list = []  # Lista pomieszczeń

        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Przycisk do dodawania pomieszczeń
        add_room_button = Button(text="Dodaj pomieszczenie", size_hint_y=None, height=50)
        add_room_button.bind(on_press=self.show_add_room_popup)
        layout.add_widget(add_room_button)

        # Przycisk do wyszukiwania urządzeń
        search_button = Button(text="Szukaj urządzeń", size_hint_y=None, height=50)
        search_button.bind(on_press=self.search_devices)
        layout.add_widget(search_button)

        # Przycisk do ręcznego dodawania urządzeń
        add_device_button = Button(text="Dodaj urządzenie ręcznie", size_hint_y=None, height=50)
        add_device_button.bind(on_press=self.show_add_device_popup)
        layout.add_widget(add_device_button)

        # ScrollView do wyświetlania listy urządzeń
        self.device_list_layout = BoxLayout(orientation='vertical', size_hint_y=None)
        self.device_list_layout.bind(minimum_height=self.device_list_layout.setter('height'))
        device_scroll_view = ScrollView(size_hint=(1, None), height=200)
        device_scroll_view.add_widget(self.device_list_layout)
        layout.add_widget(device_scroll_view)

        return layout

    def show_add_room_popup(self, instance):
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)

        # Pole do wprowadzenia nazwy pomieszczenia
        self.room_input = TextInput(hint_text="Wprowadź nazwę pomieszczenia", size_hint_y=None, height=50)
        content.add_widget(self.room_input)

        # Przycisk do dodania pomieszczenia
        add_button = Button(text="Dodaj", size_hint_y=None, height=50)
        add_button.bind(on_press=self.add_room)
        content.add_widget(add_button)

        # Przycisk do zamknięcia popupu
        back_button = Button(text="Wróć", size_hint_y=None, height=50)
        back_button.bind(on_press=self.close_popup)
        content.add_widget(back_button)

        # Tworzenie popupu
        self.popup = Popup(title="Dodaj pomieszczenie", content=content, size_hint=(0.8, 0.8))
        self.popup.open()

    def show_add_device_popup(self, instance):
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)

        # Pole do wprowadzenia adresu IP urządzenia
        self.device_ip_input = TextInput(hint_text="Wprowadź adres IP urządzenia", size_hint_y=None, height=50)
        content.add_widget(self.device_ip_input)

        # Przycisk do dodania urządzenia ręcznie
        add_button = Button(text="Dodaj", size_hint_y=None, height=50)
        add_button.bind(on_press=self.add_device_manually)
        content.add_widget(add_button)

        # Przycisk do zamknięcia popupu
        back_button = Button(text="Wróć", size_hint_y=None, height=50)
        back_button.bind(on_press=self.close_popup)
        content.add_widget(back_button)

        # Tworzenie popupu
        self.popup = Popup(title="Dodaj urządzenie ręcznie", content=content, size_hint=(0.8, 0.8))
        self.popup.open()

    def add_room(self, instance):
        room_name = self.room_input.text.strip()
        if room_name:
            self.room_list.append(room_name)
            self.room_input.text = ""
            self.close_popup()

    def add_device_manually(self, instance):
        device_ip = self.device_ip_input.text.strip()
        if device_ip:
            self.device_list.append(f"Urządzenie ręczne: {device_ip}")
            self.update_device_list_ui(f"Urządzenie ręczne: {device_ip}")
            self.close_popup()
            self.get_device_info(device_ip)  # Próbujemy pobrać dane o urządzeniu z sieci

    def close_popup(self):
        if hasattr(self, 'popup'):
            self.popup.dismiss()

    def search_devices(self, instance):
        print("Wyszukiwanie urządzeń w sieci Wi-Fi...")
        self.zeroconf = Zeroconf()
        self.browser = ServiceBrowser(self.zeroconf, "_http._tcp.local.", handlers=[self.on_service_state_change])

    def on_service_state_change(self, zeroconf, service_type, name, state_change):
        if state_change == ServiceStateChange.Added:
            print(f"Znaleziono urządzenie: {name}")
            device_type = self.filter_device_type(name)  # Filtrowanie typu urządzenia
            self.device_list.append(f"{device_type}: {name}")
            self.update_device_list_ui(f"{device_type}: {name}")
        elif state_change == ServiceStateChange.Removed:
            print(f"Urządzenie {name} zostało usunięte z sieci")

    def filter_device_type(self, name):
        """Prosta funkcja do filtrowania urządzeń na podstawie ich nazw (można dostosować do własnych potrzeb)"""
        if "camera" in name.lower():
            return "Kamera"
        elif "thermostat" in name.lower():
            return "Termostat"
        elif "light" in name.lower():
            return "Światło"
        else:
            return "Inne"

    def update_device_list_ui(self, device_name):
        # Aktualizujemy UI, aby wyświetlać znalezione urządzenie
        device_label = Label(text=device_name, size_hint_y=None, height=30)
        device_button = Button(text="Szczegóły", size_hint_y=None, height=30)
        device_button.bind(on_press=lambda instance, ip=device_name.split(": ")[-1]: self.show_device_details(ip))

        self.device_list_layout.add_widget(device_label)
        self.device_list_layout.add_widget(device_button)

    def show_device_details(self, ip):
        """Wyświetla szczegóły o urządzeniu w popupie."""
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)

        # Wstawienie etykiety z informacjami o urządzeniu
        device_info_label = Label(text=f"Szczegóły urządzenia: {ip}", size_hint_y=None, height=50)
        content.add_widget(device_info_label)

        # Przycisk do włączenia światła
        turn_on_button = Button(text="Włącz światło", size_hint_y=None, height=50)
        turn_on_button.bind(on_press=lambda instance, ip=ip: self.control_device(ip, action='on'))
        content.add_widget(turn_on_button)

        # Przycisk do wyłączenia światła
        turn_off_button = Button(text="Wyłącz światło", size_hint_y=None, height=50)
        turn_off_button.bind(on_press=lambda instance, ip=ip: self.control_device(ip, action='off'))
        content.add_widget(turn_off_button)

        # Przyciski do zamknięcia popupu
        close_button = Button(text="Zamknij", size_hint_y=None, height=50)
        close_button.bind(on_press=self.close_popup)
        content.add_widget(close_button)

        # Tworzenie popupu
        self.popup = Popup(title="Informacje o urządzeniu", content=content, size_hint=(0.8, 0.5))
        self.popup.open()

    def control_device(self, ip, action):
        """Wysyła polecenie do urządzenia, aby włączyć lub wyłączyć światło."""
        try:
            url = f"http://{ip}/control"  # Zakładamy, że urządzenia obsługują tę ścieżkę
            data = {"action": action}  # Dane do wysłania w żądaniu
            response = requests.post(url, json=data)
            if response.status_code == 200:
                print(f"Polecenie '{action}' wysłane do {ip}.")
            else:
                print(f"Błąd w komunikacji z {ip}: {response.status_code}")
        except requests.RequestException as e:
            print(f"Błąd komunikacji z urządzeniem {ip}: {e}")

    def get_device_info(self, ip):
        """Pobieramy informacje o urządzeniu za pomocą protokołu HTTP"""
        try:
            response = requests.get(f"http://{ip}")
            if response.status_code == 200:
                print(f"Informacje o urządzeniu z {ip}: {response.text}")
            else:
                print(f"Brak odpowiedzi z urządzenia {ip}")
        except requests.RequestException as e:
            print(f"Błąd komunikacji z urządzeniem {ip}: {e}")


if __name__ == '__main__':
    SmartHomeApp().run()
