import streamlit as st
from datetime import datetime
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
import gspread
from gspread_dataframe import set_with_dataframe
import locale

try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except:
    locale.setlocale(locale.LC_ALL, '')

class streamlit_app:
    def __init__(self):
        self.configure_page()
        self.initialize_google_sheets()
        self.load_excel_data()
        
    def configure_page(self):
        st.set_page_config(page_title="Disponibilização de Dotação", layout="centered")
        
        st.markdown("""
            <style>
            .stTextInput > div > div > input {
                background-color: white;
                color: black;
            }
            .stButton > button {
                background-color: #00513F;
                color: grey;
                width: 100%;
                height: 50px;
                margin-top: 20px;
            }
            .main > div {
                padding: 2rem;
                max-width: 800px;
                margin: 0 auto;
                background-color: #1E1E1E;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            div[data-testid="stSelectbox"] {
                background-color: grey;
                color: black !important;
                padding: 5px;
                border-radius: 4px;
                margin: 10px 0;
            }
            .stDateInput > div > div > input {
                background-color: white;
                color: black;
            }
            h1, h2, h3, label, p {
                color: white !important;
            }
            div[data-baseweb="select"] > div {
                background-color: white;
                color: black;
            }
            </style>
            """, unsafe_allow_html=True)

    def initialize_google_sheets(self):
        try:
            credentials = service_account.Credentials.from_service_account_file(
                'credentials.json',
                scopes=[
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/drive'
                ]
            )
            
            self.gc = gspread.authorize(credentials)
            self.service_account_email = credentials.service_account_email
            self.SHEET_ID = '1Gx5-Fd5lW0tO18jwiKilRN3OVjOPoD2t0GSSnpEKvmQ'
            
            try:
                spreadsheet = self.gc.open_by_key(self.SHEET_ID)
                
                try:
                    self.worksheet = spreadsheet.worksheet('Registros')
                except gspread.WorksheetNotFound:
                    self.worksheet = spreadsheet.add_worksheet('Registros', 1000, 20)
                    headers = ['Data', 'Órgão', 'Dotação', 'Sequencial', 'Valor']
                    self.worksheet.append_row(headers)
                
                st.success(f"Conectado à planilha: {spreadsheet.title}")
                
            except gspread.exceptions.APIError as e:
                if '404' in str(e):
                    st.error(f"""
                        Planilha não encontrada. Verifique:
                        1. ID da planilha: {self.SHEET_ID}
                        2. Compartilhamento com: {self.service_account_email}
                        """)
                raise
                
        except Exception as e:
            st.error(f"Erro ao inicializar Google Drive: {str(e)}")
            raise

    def load_excel_data(self):
        try:
            self.df = pd.read_excel('/workspaces/gdp-dashboard/data/DOTACOES.xlsx')
            self.orgaos = sorted(self.df['ÓRGÃO'].unique())
            return True
        except Exception as e:
            st.error(f"Erro ao carregar o arquivo Excel: {str(e)}")
            return False

    def format_currency(self, value):
        try:
            return locale.currency(float(value), grouping=True, symbol='R$')
        except:
            return f"R$ {value}"

    def save_to_google_sheets(self, data):
        try:
            row_data = [
                data['Data'],
                str(data['Órgão']),
                str(data['Dotação']),
                int(data['Sequencial']),
                str(data['Valor'])
            ]
            
            self.worksheet.append_row(row_data)
            return True
            
        except gspread.exceptions.APIError as e:
            if '404' in str(e):
                raise Exception(f"Planilha não encontrada. Verifique se {self.service_account_email} tem acesso.")
            raise Exception(f"Erro na API do Google Sheets: {str(e)}")
        except Exception as e:
            raise Exception(f"Erro ao salvar na planilha: {str(e)}")

    def run(self):
        st.title("Disponibilização de Dotação")
        
        if not hasattr(self, 'df'):
            return

        if 'selected_orgao' not in st.session_state:
            st.session_state.selected_orgao = None
        if 'selected_dotacao' not in st.session_state:
            st.session_state.selected_dotacao = None

        selected_orgao = st.selectbox(
            "Selecione o Órgão",
            options=[''] + self.orgaos,
            index=0
        )

        if selected_orgao != st.session_state.selected_orgao:
            st.session_state.selected_orgao = selected_orgao
            st.session_state.selected_dotacao = None

        if selected_orgao:
            dotacoes_filtered = self.df[self.df['ÓRGÃO'] == selected_orgao]
            dotacoes = sorted(dotacoes_filtered['DOTAÇÃO'].unique())
            
            selected_dotacao = st.selectbox(
                "Selecione a Dotação",
                options=[''] + dotacoes,
                index=0
            )

            if selected_dotacao != st.session_state.selected_dotacao:
                st.session_state.selected_dotacao = selected_dotacao

            if selected_dotacao:
                sequenciais = sorted(
                    dotacoes_filtered[dotacoes_filtered['DOTAÇÃO'] == selected_dotacao]['SEQUENCIAL'].unique()
                )
                selected_sequencial = st.selectbox(
                    "Selecione o Sequencial",
                    options=sequenciais
                )

                st.markdown("### Insira abaixo o valor disponibilizado")
                valor = st.text_input(
                    "Digite o valor (R$)",
                    key="value_input",
                    help="Digite o valor em reais (ex: 1.000,00)"
                )

                st.markdown("### Data da Disponibilização")
                data = st.date_input(
                    label="Data",
                    value=datetime.now(),
                    format="DD/MM/YYYY",
                    label_visibility="collapsed"
                )

                if st.button("ENVIAR PARA SMO"):
                    if valor:
                        try:
                            valor_float = float(valor.replace('.', '').replace(',', '.'))
                            
                            registro = {
                                'Data': data.strftime('%d/%m/%Y'),
                                'Órgão': selected_orgao,
                                'Dotação': selected_dotacao,
                                'Sequencial': selected_sequencial,
                                'Valor': self.format_currency(valor_float)
                            }
                            
                            if self.save_to_google_sheets(registro):
                                st.success(f"""Dados enviados com sucesso!
                                    Valor registrado: {self.format_currency(valor_float)}
                                    Data: {data.strftime('%d/%m/%Y')}""")
                            
                        except ValueError:
                            st.error("Por favor, insira um valor numérico válido (ex: 1.000,00)")
                        except Exception as e:
                            st.error(f"Erro ao enviar dados: {str(e)}")
                    else:
                        st.warning("Por favor, preencha o valor.")

if __name__ == "__main__":
    app = streamlit_app()
    app.run()