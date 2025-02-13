# Arquivo: crude.py
# Data: 13/02/2025 - 14:52
# IDE Cursor - claude 3.5 sonnet
# nova coluna section

import streamlit as st
import pandas as pd
import sqlite3

# Nome do banco de dados
DB_NAME = "calcpc.db"

def format_br_number(value):
    """Formata um número para o padrão brasileiro."""
    try:
        if pd.isna(value) or value == '':
            return ''
        return f"{float(str(value).replace(',', '.')):.2f}".replace('.', ',')
    except:
        return ''

def show_crud():
    """Exibe registros administrativos em formato de tabela."""
    st.title("Lista de Registros ADM")
    
    if st.button("Atualizar Dados"):
        st.rerun()
    
    # Seleção da tabela com opção vazia inicial
    st.write("Selecione a tabela:")
    tables = ["", "forms_tab", "forms_insumos", "forms_resultados"]
    selected_table = st.selectbox(
        "Selecione a tabela", 
        tables, 
        key="table_selector"
    )
    
    # Só processa se uma tabela foi selecionada
    if selected_table:
        # Conexão com o banco
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        try:
            # Busca informações da estrutura da tabela
            cursor.execute(f"PRAGMA table_info({selected_table})")
            columns_info = cursor.fetchall()
            
            # Conta registros
            cursor.execute(f"SELECT COUNT(*) FROM {selected_table}")
            total_records = cursor.fetchone()[0]
            
            # Exibe informações da tabela
            st.write("### Informações da Tabela")
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Total de Registros:** {total_records}")
                st.write(f"**Quantidade de Campos:** {len(columns_info)}")
            
            # Exibe estrutura dos campos
            st.write("### Estrutura dos Campos")
            fields_df = pd.DataFrame(
                [(col[1], col[2]) for col in columns_info],
                columns=['Campo', 'Tipo']
            )
            st.dataframe(fields_df, use_container_width=True)
            
            # Busca e exibe os dados
            cursor.execute(f"SELECT * FROM {selected_table}")
            data = cursor.fetchall()
            columns = [col[1] for col in columns_info]
            
            st.write("### Dados da Tabela")
            df = pd.DataFrame(data, columns=columns)
            
            # Formata a coluna value_element para o padrão brasileiro
            if 'value_element' in df.columns:
                df['value_element'] = df['value_element'].apply(
                    lambda x: format_br_number(x) if pd.notnull(x) else ''
                )
            
            st.dataframe(df, use_container_width=True)
            
            # Botão de download - mantém o formato original para exportação
            if not df.empty:
                export_df = df.copy()
                if 'value_element' in export_df.columns:
                    export_df['value_element'] = export_df['value_element'].apply(
                        lambda x: format_br_number(x) if pd.notnull(x) else ''
                    )
                
                txt_data = export_df.to_csv(
                    sep='\t',
                    index=False,
                    encoding='cp1252'
                )
                
                st.download_button(
                    label="Download TXT",
                    data=txt_data.encode('cp1252'),
                    file_name=f"{selected_table}.txt",
                    mime="text/plain"
                )
        
        except Exception as e:
            st.error(f"Erro ao processar dados: {str(e)}")
        
        finally:
            conn.close()

# Remover ou comentar a função app() se não estiver sendo usada
# def app():
#     """Função principal que será chamada pelo main.py"""
#     show_admin_records()
