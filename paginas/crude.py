# Arquivo: crude.py
# Data: 15/07/2025  16:00
# IDE Cursor - claude 3.5 sonnet
# Adaptação para o uso de Discos SSD e a pasta Data para o banco de dados
# Download do arquivo calcpc.db

import streamlit as st
import pandas as pd
import sqlite3
import os
from pathlib import Path
from typing import List, Any, Dict, Tuple

from config import DB_PATH  # Adicione esta importação

# Constantes
COLUMN_WIDTHS = {
    'usuarios': {
        'id': 'small',
        'user_id': 'small',
        'nome': 'medium',
        'email': 'medium',
        'senha': 'small',
        'perfil': 'small',
        'empresa': 'medium'
    },
    'forms_tab': {
        'ID_element': 'small',
        'name_element': 'small',
        'type_element': 'small',
        'math_element': 'small',
        'msg_element': 'medium',
        'value_element': 'small',
        'select_element': 'small',
        'str_element': 'medium',
        'e_col': 'small',
        'e_row': 'small',
        'user_id': 'small',
        'section': 'small',
        'col_len': 'small'
    },
    'forms_insumos': {
        'ID_element': 'small',
        'name_element': 'medium',
        'type_element': 'small',
        'math_element': 'small',
        'msg_element': 'medium',
        'value_element': 'medium',
        'select_element': 'medium',
        'str_element': 'medium',
        'e_col': 'small',
        'e_row': 'small',
        'user_id': 'small'
    },
    'forms_resultados': {
        'ID_element': 'small',
        'name_element': 'medium',
        'type_element': 'small',
        'math_element': 'small',
        'msg_element': 'medium',
        'value_element': 'small',
        'select_element': 'medium',
        'str_element': 'medium',
        'e_col': 'small',
        'e_row': 'small',
        'user_id': 'small'
    },
    'forms_result_sea': {
        'ID_element': 'small',
        'name_element': 'medium',
        'type_element': 'small',
        'math_element': 'small',
        'msg_element': 'medium',
        'value_element': 'small',
        'select_element': 'medium',
        'str_element': 'medium',
        'e_col': 'small',
        'e_row': 'small',
        'user_id': 'small'
    },
    'forms_setorial': {
        'ID_element': 'small',
        'name_element': 'medium',
        'type_element': 'small',
        'math_element': 'small',
        'msg_element': 'medium',
        'value_element': 'small',
        'select_element': 'medium',
        'str_element': 'medium',
        'e_col': 'small',
        'e_row': 'small',
        'user_id': 'small'
    },
    'forms_setorial_sea': {
        'ID_element': 'small',
        'name_element': 'medium',
        'type_element': 'small',
        'math_element': 'small',
        'msg_element': 'medium',
        'value_element': 'small',
        'select_element': 'medium',
        'str_element': 'medium',
        'e_col': 'small',
        'e_row': 'small',
        'user_id': 'small'
    },
    'forms_energetica': {
        'ID_element': 'small',
        'name_element': 'medium',
        'type_element': 'small',
        'math_element': 'small',
        'msg_element': 'medium',
        'value_element': 'small',
        'select_element': 'medium',
        'str_element': 'medium',
        'e_col': 'small',
        'e_row': 'small',
        'user_id': 'small'
    },
    'log_acessos': {
        'id': 'small',
        'user_id': 'small',
        'data_acesso': 'small',
        'programa': 'medium',
        'acao': 'medium'
    }
}

TABLES_LIST = ["", "usuarios", "forms_tab", "forms_insumos", "forms_resultados", 
               "forms_result_sea", "forms_setorial", "forms_setorial_sea", 
               "forms_energetica", "log_acessos"]

def format_br_number(value):
    """Formata um número para o padrão brasileiro."""
    try:
        if pd.isna(value) or value == '':
            return ''
        return f"{float(str(value).replace(',', '.')):.2f}".replace('.', ',')
    except:
        return ''

def get_table_analysis(cursor, table_name):
    """Analisa a estrutura e dados da tabela."""
    # Análise da estrutura
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns_info = cursor.fetchall()
    
    # Contagem de registros
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    record_count = cursor.fetchone()[0]
    
    # Data da última atualização (assumindo que existe uma coluna 'data' ou similar)
    try:
        cursor.execute(f"SELECT MAX(data) FROM {table_name}")
        last_update = cursor.fetchone()[0]
    except:
        last_update = "N/A"
    
    # Maior user_id
    try:
        cursor.execute(f"SELECT MAX(user_id) FROM {table_name}")
        max_user_id = cursor.fetchone()[0]
    except:
        max_user_id = "N/A"
    
    return {
        "columns": columns_info,
        "record_count": record_count,
        "last_update": last_update,
        "max_user_id": max_user_id
    }

def show_download_calcpc_button():
    """Exibe o botão de download do arquivo calcpc.db."""
    calcpc_path = Path("data/calcpc.db")
    if calcpc_path.exists():
        with open(calcpc_path, "rb") as file:
            st.download_button(
                label="📥 Download calcpc.db",
                data=file.read(),
                file_name="calcpc.db",
                mime="application/octet-stream",
                help="Clique para baixar o arquivo calcpc.db da pasta data"
            )
    else:
        st.warning("⚠️ Arquivo 'calcpc.db' não encontrado na pasta 'data'")

def show_table_selector():
    """Exibe o seletor de tabelas."""
    col1, col2, col3 = st.columns([3.5, 3, 3.5])
    with col2:
        return st.selectbox("Selecione a tabela", TABLES_LIST, key="table_selector")

def show_table_info(cursor, selected_table, analysis):
    """Exibe informações da tabela em um expander."""
    with st.expander("Informações da Tabela", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de Registros", analysis["record_count"])
        with col2:
            if selected_table == "log_acessos":
                cursor.execute("SELECT COUNT(DISTINCT user_id) FROM log_acessos")
                unique_users = cursor.fetchone()[0]
                st.metric("Usuários Únicos", unique_users)
            else:
                st.metric("Última Atualização", analysis["last_update"])
        with col3:
            if selected_table == "log_acessos":
                cursor.execute("SELECT COUNT(DISTINCT data_acesso) FROM log_acessos")
                unique_dates = cursor.fetchone()[0]
                st.metric("Dias com Registros", unique_dates)
            else:
                st.metric("Maior User ID", analysis["max_user_id"])
        
        # Exibe estrutura da tabela
        st.write("### Estrutura da Tabela")
        structure_df = pd.DataFrame(
            analysis["columns"],
            columns=["cid", "name", "type", "notnull", "dflt_value", "pk"]  # type: ignore
        )
        st.dataframe(
            structure_df[["name", "type", "notnull", "pk"]],
            hide_index=True,
            use_container_width=True
        )

def get_log_acessos_data(cursor):
    """Busca dados específicos para log_acessos."""
    cursor.execute("""
        SELECT 
            id as 'id',
            user_id as 'user_id',
            data_acesso as 'data_acesso',
            programa as 'programa',
            acao as 'acao',
            time(hora_acesso) as 'hora_acesso'
        FROM log_acessos 
        ORDER BY data_acesso DESC, hora_acesso DESC, id DESC
    """)
    return cursor.fetchall(), ['id', 'user_id', 'data_acesso', 'programa', 'acao', 'hora_acesso']

def get_forms_tab_data(cursor):
    """Busca dados específicos para forms_tab com filtros."""
    user_id_filter = st.number_input("Filtrar por User ID (0 para mostrar todos)", min_value=0, value=0)
    
    sort_column = st.selectbox(
        "Ordenar por coluna",
        ["ID_element", "name_element", "type_element", "e_col", "e_row", "user_id", "section"],
        index=0
    )
    sort_order = st.selectbox("Ordem", ["ASC", "DESC"], index=0)
    
    query = f"""
        SELECT * FROM forms_tab
        {f"WHERE user_id = {user_id_filter}" if user_id_filter > 0 else ""}
        ORDER BY {sort_column} {sort_order}
    """
    cursor.execute(query)
    return cursor.fetchall()

def get_column_config_for_log_acessos():
    """Retorna configuração de colunas específica para log_acessos."""
    return {
        "id": st.column_config.NumberColumn(
            "id",
            width="small",
            required=True,
        ),
        "user_id": st.column_config.NumberColumn(
            "user_id",
            width="small",
            required=True,
        ),
        "data_acesso": st.column_config.TextColumn(
            "data_acesso",
            width="medium",
            required=True,
            help="Formato: YYYY-MM-DD"
        ),
        "programa": st.column_config.TextColumn(
            "programa",
            width="medium",
            required=True,
        ),
        "acao": st.column_config.TextColumn(
            "acao",
            width="medium",
            required=True,
        ),
        "hora_acesso": st.column_config.TextColumn(
            "hora_acesso",
            width="small",
            required=False,
            help="Formato: HH:MM:SS"
        )
    }

def get_column_config_for_table(selected_table, columns_info):
    """Retorna configuração de colunas para uma tabela específica."""
    column_config = {}
    
    for col_info in columns_info:
        col_name = col_info[1]
        col_type = col_info[2].upper()
        column_width = COLUMN_WIDTHS.get(selected_table, {}).get(col_name, 'medium')
        
        if selected_table == "usuarios":
            if col_name == "perfil":
                column_config[col_name] = st.column_config.SelectboxColumn(
                    "perfil",
                    width=column_width,  # type: ignore
                    required=True,
                    options=["adm", "usuario", "Gestor", "master"]
                )
            elif col_name == "email":
                column_config[col_name] = st.column_config.TextColumn(
                    "email",
                    width=column_width,  # type: ignore
                    required=True
                )
            else:
                if 'INTEGER' in col_type:
                    column_config[col_name] = st.column_config.NumberColumn(
                        col_name,
                        width=column_width,  # type: ignore
                        required=True,
                    )
                else:
                    column_config[col_name] = st.column_config.TextColumn(
                        col_name,
                        width=column_width,  # type: ignore
                        required=True
                    )
        else:
            if 'INTEGER' in col_type:
                column_config[col_name] = st.column_config.NumberColumn(
                    col_name,
                    width=column_width,  # type: ignore
                    required=True,
                )
            elif 'REAL' in col_type:
                column_config[col_name] = st.column_config.NumberColumn(
                    col_name,
                    width=column_width,  # type: ignore
                    required=True,
                )
            else:
                column_config[col_name] = st.column_config.TextColumn(
                    col_name,
                    width=column_width,  # type: ignore
                    required=True
                )
    
    return column_config

def validate_forms_tab_duplicates(edited_df):
    """Valida duplicatas na tabela forms_tab."""
    duplicates = edited_df[edited_df['ID_element'].duplicated(keep=False)]
    if not duplicates.empty:
        st.error(f"⚠️ Encontradas duplicatas de ID_element no editor: {duplicates['ID_element'].tolist()}")
        return False
    return True

def insert_new_records(cursor, selected_table, edited_df, df, columns):
    """Insere novos registros na tabela."""
    if len(edited_df) > len(df):
        new_records = edited_df.iloc[len(df):]
        for _, row in new_records.iterrows():
            if selected_table == 'forms_tab':
                st.write(f"Tentando inserir ID_element: {row['ID_element']}")
                
                cursor.execute("""
                    SELECT ID_element, rowid 
                    FROM forms_tab 
                    WHERE ID_element = ?
                """, (row['ID_element'],))
                existing = cursor.fetchone()
                
                if existing:
                    st.error(f"⚠️ Não é possível adicionar: O ID_element '{row['ID_element']}' já existe na linha {existing[1]}")
                    continue

            row_values = [row[col] for col in columns]
            insert_query = f"""
            INSERT INTO {selected_table} ({', '.join(columns)})
            VALUES ({', '.join(['?' for _ in columns])})
            """
            cursor.execute(insert_query, tuple(row_values))

def update_existing_records(cursor, selected_table, edited_df, df, columns):
    """Atualiza registros existentes na tabela."""
    for index, row in edited_df.iloc[:len(df)].iterrows():
        if selected_table == 'forms_tab':
            cursor.execute("""
                SELECT ID_element, rowid 
                FROM forms_tab 
                WHERE ID_element = ? 
                    AND user_id = ?
                    AND ID_element != (
                        SELECT ID_element 
                        FROM forms_tab 
                        WHERE ID_element = ?
                        AND user_id = ?
                    )
            """, (row['ID_element'], row['user_id'], row['ID_element'], row['user_id']))
            
            existing = cursor.fetchone()
            if existing:
                st.error(f"⚠️ Não é possível atualizar: O ID_element '{row['ID_element']}' já está sendo usado em outro registro com o mesmo user_id")
                continue

        if selected_table == 'forms_tab':
            update_query = f"""
            UPDATE {selected_table}
            SET {', '.join(f'{col} = ?' for col in columns)}
            WHERE ID_element = ? AND user_id = ?
            """
            values = tuple(row) + (row['ID_element'], row['user_id'])
        else:
            update_query = f"""
            UPDATE {selected_table}
            SET {', '.join(f'{col} = ?' for col in columns)}
            WHERE rowid = {index + 1}
            """
            values = tuple(row)
            
        cursor.execute(update_query, values)

def save_changes(cursor, selected_table, edited_df, df, columns):
    """Salva as alterações na tabela."""
    try:
        if selected_table == 'forms_tab' and not validate_forms_tab_duplicates(edited_df):
            return

        insert_new_records(cursor, selected_table, edited_df, df, columns)
        update_existing_records(cursor, selected_table, edited_df, df, columns)
        
        # Commit das alterações no banco de dados
        cursor.connection.commit()
        
        st.success("Alterações salvas com sucesso!")
        st.rerun()
    
    except Exception as e:
        st.error(f"Erro ao salvar alterações: {str(e)}")

def export_table_data(edited_df, selected_table):
    """Exporta dados da tabela para arquivo TXT."""
    if not edited_df.empty:
        export_df = edited_df.copy()
        
        # Procura pela coluna que contém 'value' no nome
        value_columns = [col for col in export_df.columns if 'value' in col.lower()]
        
        # Converte os números para string e substitui ponto por vírgula
        for value_col in value_columns:
            export_df[value_col] = export_df[value_col].apply(lambda x: str(x).replace('.', ',') if pd.notnull(x) else '')
        
        # Desativa a formatação automática do pandas para números
        txt_data = export_df.to_csv(sep='\t', index=False, encoding='cp1252', float_format=None)
        st.download_button(
            label="Download TXT",
            data=txt_data.encode('cp1252'),
            file_name=f"{selected_table}.txt",
            mime="text/plain"
        )

def process_table_data(cursor, selected_table):
    """Processa e exibe dados da tabela selecionada."""
    # Análise da tabela
    analysis = get_table_analysis(cursor, selected_table)
    
    # Obtém informações das colunas
    cursor.execute(f"PRAGMA table_info({selected_table})")
    columns_info = cursor.fetchall()
    
    # Exibe informações da tabela
    show_table_info(cursor, selected_table, analysis)
    
    # Busca dados específicos da tabela
    if selected_table == "log_acessos":
        data, columns = get_log_acessos_data(cursor)
        # Converte para tipos específicos para evitar problemas de tipo
        df = pd.DataFrame(data, columns=columns)  # type: ignore
        if 'data_acesso' in df.columns:
            df['data_acesso'] = df['data_acesso'].astype(str)
        column_config = get_column_config_for_log_acessos()
    elif selected_table == "forms_tab":
        data = get_forms_tab_data(cursor)
        cursor.execute(f"PRAGMA table_info({selected_table})")
        columns = [col[1] for col in cursor.fetchall()]
        # Converte para tipos específicos para evitar problemas de tipo
        df = pd.DataFrame(data, columns=columns)  # type: ignore
        column_config = get_column_config_for_table(selected_table, columns_info)
    else:
        cursor.execute(f"SELECT * FROM {selected_table}")
        data = cursor.fetchall()
        cursor.execute(f"PRAGMA table_info({selected_table})")
        columns = [col[1] for col in cursor.fetchall()]
        # Converte para tipos específicos para evitar problemas de tipo
        df = pd.DataFrame(data, columns=columns)  # type: ignore
        column_config = get_column_config_for_table(selected_table, columns_info)
    
    # Converte para formato editável
    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        column_config=column_config,
        hide_index=False,
        key=f"editor_{selected_table}"
    )
    
    # Botão para salvar alterações
    if st.button("Salvar Alterações"):
        save_changes(cursor, selected_table, edited_df, df, columns)
    
    # Botão de exportação
    export_table_data(edited_df, selected_table)

def show_crud():
    """Exibe registros administrativos em formato de tabela."""
    st.title("Lista de Registros ADM")
    
    # Botão para download do arquivo calcpc.db
    show_download_calcpc_button()
    
    if st.button("Atualizar Dados"):
        st.rerun()
    
    # Seletor de tabelas
    selected_table = show_table_selector()
    
    if selected_table:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        try:
            process_table_data(cursor, selected_table)
        except Exception as e:
            st.error(f"Erro ao processar dados: {str(e)}")
        finally:
            conn.close()

