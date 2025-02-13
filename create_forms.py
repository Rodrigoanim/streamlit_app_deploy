# Arquivo: create_forms.py
# Data: 13/02/2025 - 14:39
# Descrição: Script para atualizar atraves de um arquivo .txt
# Cursor - Claude 3.5 Sonnet
# Coluna: value_element = real
# Programa roda direto no Python - não usar o streamlit


import sqlite3
import os
import pandas as pd
from tkinter import filedialog, messagebox
import tkinter as tk

# Nome do banco de dados
DB_NAME = "calcpc.db"

def clean_string(value):
    """Limpa strings de aspas e apóstrofos extras."""
    if isinstance(value, str):
        return value.replace("'", "").replace('"', "").strip()
    return value

def clean_csv_data(txt_file):
    """Limpa e prepara os dados do TXT tabulado em ANSI."""
    try:
        # Lê o arquivo tabulado em ANSI (cp1252)
        df = pd.read_csv(
            txt_file, 
            index_col=0,
            encoding='cp1252',  # Codificação ANSI/Windows-1252
            sep='\t',          # Separador de tabulação
            quoting=3,         # QUOTE_NONE
            na_filter=False,   # Não converte strings vazias para NaN
            decimal=','        # Define vírgula como separador decimal
        )
        print("Arquivo lido com sucesso usando ANSI e tabulação")
        
        # Remove aspas extras e espaços
        for column in df.columns:
            if df[column].dtype == 'object':
                df[column] = df[column].apply(lambda x: str(x).strip('"\'').strip() if pd.notna(x) else '')
        
        # Debug: mostra as primeiras linhas após limpeza
        print("\nPrimeiras linhas após limpeza:")
        print(df.head())
        
        return df
        
    except Exception as e:
        print(f"Erro ao limpar dados: {str(e)}")
        print(f"Tipo do erro: {type(e)}")
        return None

def format_float_value(value):
    """Converte valor para float, usando padrão brasileiro (vírgula como decimal e ponto como milhar)."""
    try:
        # Se valor for vazio ou None
        if not value and value != 0:
            return 0.0
            
        # Se já for float, retorna diretamente
        if isinstance(value, float):
            return value
            
        # Converte para string e remove espaços
        str_value = str(value).strip()
        
        # Remove pontos de milhar e substitui vírgula por ponto decimal para cálculo
        str_value = str_value.replace('.', '').replace(',', '.')
        
        # Se após limpeza ficar vazio
        if not str_value:
            return 0.0
            
        # Converte para float
        float_value = float(str_value)
        
        return float_value
        
    except Exception as e:
        print(f"Erro ao formatar valor numérico: {value}. Erro: {str(e)}")
        return 0.0

def format_br_number(value):
    """Formata um número float para o padrão brasileiro (vírgula como decimal)."""
    try:
        return f"{float(value)}".replace('.', ',')
    except:
        return '0,0'

def validate_selectbox_data(row):
    """Valida e corrige dados do selectbox."""
    try:
        if row['type_element'] == 'selectbox':
            # Força math_element para '0,0' em selectbox
            row['math_element'] = '0,0'
            
            # Limpa select_element
            if pd.notna(row['select_element']):
                options = row['select_element'].replace('"', '').replace("'", '').strip()
                options_list = [opt.strip() for opt in options.split('|')]
                row['select_element'] = '|'.join(options_list)
            else:
                row['select_element'] = ''
            
            # Limpa str_element
            if pd.notna(row['str_element']):
                str_value = row['str_element'].replace('"', '').replace("'", '').strip()
                row['str_element'] = str_value
            else:
                row['str_element'] = ''
            
            # Força value_element para 0.0
            row['value_element'] = 0.0
            print(f"Valor do selectbox definido como: {format_br_number(row['value_element'])}")
        else:
            # Trata value_element e registra valores problemáticos
            original_value = row['value_element']
            row['value_element'] = format_float_value(original_value)
            
            # Registra conversões para zero que não eram zero originalmente
            if row['value_element'] == 0.0 and str(original_value).strip() not in ['0', '0,0', '']:
                print(f"Aviso: Valor original '{original_value}' foi convertido para '{format_br_number(0.0)}'")
            else:
                print(f"Valor convertido: {format_br_number(row['value_element'])}")
            
        return True, row
    except Exception as e:
        print(f"Erro ao validar selectbox: {str(e)}")
        return False, row

def select_table():
    """Permite ao usuário selecionar a tabela para importação."""
    root = tk.Tk()
    root.title("Seleção de Tabela")
    root.geometry("400x200")
    
    selected_table = tk.StringVar(value=None)
    
    def on_select():
        if selected_table.get():  # Only close if a selection was made
            root.quit()
        else:
            messagebox.showwarning("Aviso", "Por favor, selecione uma tabela")
    
    tk.Label(root, text="Selecione a tabela para importação:", pady=20).pack()
    
    tables = [
        ("Forms Principal", "forms_tab"),
        ("Forms Insumos", "forms_insumos"),
        ("Forms Resultados", "forms_resultados")
    ]
    
    for text, value in tables:
        tk.Radiobutton(root, text=text, variable=selected_table, value=value).pack()
    
    tk.Button(root, text="Confirmar", command=on_select, pady=10).pack(pady=20)
    
    root.mainloop()
    selected = selected_table.get()
    root.destroy()
    
    return selected if selected else "forms_tab"  # Retorna forms_tab como padrão se nada for selecionado

def create_database():
    """Cria o banco de dados e a tabela selecionada."""
    # Solicita a seleção da tabela
    table_name = select_table()
    
    conn = None
    try:
        # Verifica banco existente
        if os.path.exists(DB_NAME):
            root = tk.Tk()
            root.withdraw()
            if messagebox.askyesno("Confirmação", 
                f"A tabela {table_name} já existe. Deseja apagá-la e criar uma nova?"):
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
                conn.commit()
                print(f"Tabela {table_name} removida para recriação.")
            else:
                print("Operação cancelada pelo usuário.")
                return
        else:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

        # Se conn ainda não foi definido, criar conexão
        if not conn:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

        # Cria tabela
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                ID_element INTEGER PRIMARY KEY AUTOINCREMENT,
                name_element TEXT NOT NULL,
                type_element TEXT NOT NULL,
                math_element TEXT,
                msg_element TEXT,
                value_element REAL,
                select_element TEXT,
                str_element TEXT,
                e_col INTEGER,
                e_row INTEGER,
                user_id INTEGER,
                section TEXT
            );
        """)

        # Seleciona arquivo
        root = tk.Tk()
        root.withdraw()
        txt_file = filedialog.askopenfilename(
            title=f"Selecione o arquivo CSV/TXT para importar em {table_name}",
            filetypes=[("CSV/Text files", "*.csv;*.txt")]
        )

        if txt_file:
            # Limpa e prepara os dados
            df = clean_csv_data(txt_file)
            if df is None:
                return

            # Processa cada linha
            for _, row in df.iterrows():
                row_dict = row.to_dict()
                
                # Valida dados do selectbox
                is_valid, row_dict = validate_selectbox_data(row_dict)
                if not is_valid:
                    continue
                
                try:
                    cursor.execute(f"""
                        INSERT INTO {table_name} (
                            name_element, type_element, math_element, 
                            msg_element, value_element, select_element,
                            str_element, e_col, e_row, user_id, section
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        str(row_dict['name_element']),
                        str(row_dict['type_element']),
                        str(row_dict['math_element']),
                        str(row_dict['msg_element']),
                        row_dict['value_element'],  # Mantém como float para o SQLite
                        str(row_dict['select_element']),
                        str(row_dict['str_element']),
                        int(float(format_float_value(row_dict['e_col']))),
                        int(float(format_float_value(row_dict['e_row']))),
                        int(row_dict['user_id']) if pd.notna(row_dict.get('user_id')) else None,
                        str(row_dict['section']) if pd.notna(row_dict.get('section')) else None
                    ))
                    print(f"Inserido value_element: {format_br_number(row_dict['value_element'])}")
                except Exception as e:
                    print(f"Erro ao inserir linha na tabela {table_name}: {str(e)}")
                    continue

            conn.commit()
            print(f"Dados importados com sucesso para a tabela '{table_name}' do arquivo '{txt_file}'")
        else:
            print("Nenhum arquivo selecionado.")

    except Exception as e:
        print(f"Erro: {str(e)}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    create_database()
