import requests
from bs4 import BeautifulSoup
import csv
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.core.text import LabelBase
import arabic_reshaper
from bidi.algorithm import get_display

# Register the Arabic font
LabelBase.register(name='Amiri', fn_regular='Amiri-Regular.ttf')

class MatchScraperApp(App):
    def build(self):
        self.layout = BoxLayout(orientation='vertical', padding=10)
        
        self.date_input = TextInput(hint_text='Enter the date (MM/DD/YYYY)', size_hint=(1, None), height=40)
        self.layout.add_widget(self.date_input)
        
        self.scrape_button = Button(text='Scrape Matches', size_hint=(1, None), height=40)
        self.scrape_button.bind(on_press=self.scrape_matches)
        self.layout.add_widget(self.scrape_button)
        
        self.result_layout = GridLayout(cols=1, size_hint_y=None)
        self.result_layout.bind(minimum_height=self.result_layout.setter('height'))
        
        self.scroll_view = ScrollView(size_hint=(1, 1))
        self.scroll_view.add_widget(self.result_layout)
        self.layout.add_widget(self.scroll_view)
        
        return self.layout
    
    def scrape_matches(self, instance):
        date = self.date_input.text
        if not date:
            self.show_popup("Error", "Please enter a date.")
            return
        
        page = requests.get(f"https://www.yallakora.com/match-Center/?date={date}")
        matches_details = self.get_matches(page)
        
        if matches_details:
            self.save_to_csv(matches_details)
            self.display_results(matches_details)
            self.show_popup("Success", "Matches scraped and saved to CSV.")
        else:
            self.show_popup("No Matches", "No matches found for the given date.")
    
    def get_matches(self, page):
        src = page.content
        soup = BeautifulSoup(src, "lxml")
        matches_details = []
        championships = soup.find_all("div", {'class': 'matchCard'})
        
        def get_match_info(championship):
            championship_title = championship.contents[1].find("h2").text.strip()
            all_matches = championship.contents[3].find_all('div', {'class': 'item finish liItem'})
            
            for match in all_matches:
                team_A = match.find('div', {'class': 'teamA'}).text.strip()
                team_B = match.find('div', {'class': 'teamB'}).text.strip()
                
                match_results = match.find('div', {'class': 'MResult'}).find_all('span', {'class': 'score'})
                score = f"{match_results[0].text.strip()} - {match_results[1].text.strip()}"
                
                match_time = match.find('div', {'class': 'MResult'}).find('span', {'class': 'time'}).text.strip()
                
                matches_details.append({"نوع البطوله": championship_title, "الفريق الاول": team_A,
                                        "الفريق التاني": team_B, "ميعاد المباراه": match_time, "النتيجه": score})
        
        for championship in championships:
            get_match_info(championship)
        
        return matches_details
    
    def save_to_csv(self, matches_details):
        keys = matches_details[0].keys()
        with open('matches-details.csv', 'w', encoding='utf-8') as output_file:
            dict_writer = csv.DictWriter(output_file, keys)
            dict_writer.writeheader()
            dict_writer.writerows(matches_details)
    
    def display_results(self, matches_details):
        self.result_layout.clear_widgets()
        for match in matches_details:
            match_info = f"{match['نوع البطوله']} | {match['الفريق الاول']} vs {match['الفريق التاني']} | {match['ميعاد المباراه']} | {match['النتيجه']}"
            
            # Reshape and reorder Arabic text for correct display
            reshaped_text = arabic_reshaper.reshape(match_info)
            bidi_text = get_display(reshaped_text)
            
            self.result_layout.add_widget(Label(text=bidi_text, font_name='Amiri', size_hint_y=None, height=40))
    
    def show_popup(self, title, message):
        popup_layout = BoxLayout(orientation='vertical', padding=10)
        popup_label = Label(text=message)
        close_button = Button(text="Close", size_hint=(1, None), height=40)
        
        popup_layout.add_widget(popup_label)
        popup_layout.add_widget(close_button)
        
        popup = Popup(title=title, content=popup_layout, size_hint=(0.8, 0.4))
        close_button.bind(on_press=popup.dismiss)
        popup.open()

if __name__ == '__main__':
    MatchScraperApp().run()
