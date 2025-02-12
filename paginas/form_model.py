# Arquivo: form_model.py
# Data: 08/02/2025 - Hora: 15h40
# CursorAI - claude 3.5 sonnet - Composer
# 3x formualarios de entrada de dados

import sqlite3
import streamlit as st
import pandas as pd
import re

# Nome do banco de dados - calc.db
DB_NAME = "calcpc.db"

def date_to_days(date_str):
    """
    Converte uma data no formato dd/mm/aaaa para número de dias desde 01/01/1900
    """
    try:
        if not date_str:
            return 0
            
        dia, mes, ano = map(int, date_str.split('/'))
        
        # Validação básica da data
        if not (1900 <= ano <= 2100 and 1 <= mes <= 12 and 1 <= dia <= 31):
            return 0
            
        # Cálculo dos dias
        # Anos completos desde 1900
        days = (ano - 1900) * 365
        
        # Adiciona dias dos anos bissextos
        leap_years = sum(1 for y in range(1900, ano) if (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0))
        days += leap_years
        
        # Dias dos meses completos no ano atual
        days_in_month = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        if (ano % 4 == 0 and ano % 100 != 0) or (ano % 400 == 0):
            days_in_month[2] = 29
            
        days += sum(days_in_month[1:mes])
        
        # Adiciona dias do mês atual
        days += dia - 1
        
        return days
    except Exception as e:
        st.error(f"Erro na conversão de data: {str(e)}")
        return 0

def get_element_value(cursor, name_element, element=None):
    """Busca o valor de um elemento na tabela forms_tab."""
    cursor.execute("""
        SELECT value_element 
        FROM forms_tab 
        WHERE name_element = ? AND user_id = ?
    """, (name_element, st.session_state.user_id))
    result = cursor.fetchone()
    return result[0] if result and result[0] is not None else 0.0

def calculate_formula(formula, values, cursor):
    """
    Calcula o resultado de uma fórmula com suporte a operações matemáticas e datas.
    """
    try:
        # Se a fórmula for um número direto
        if isinstance(formula, (int, float)):
            return float(formula)
        
        # Se for string numérica
        if isinstance(formula, str) and formula.replace('.','',1).isdigit():
            return float(formula)
        
        # Processa referências de diferentes abas
        processed_formula = str(formula)
        
        # Verifica se é uma fórmula de data (mantém lógica existente)
        if re.match(r'^\s*[A-Z][0-9]+\s*-\s*[A-Z][0-9]+\s*$', processed_formula):
            # Extrai as duas referências
            refs = re.findall(r'[A-Z][0-9]+', processed_formula)
            if len(refs) == 2:
                # Inverte a ordem das referências para garantir data_final - data_inicial
                data_final = refs[0]  # B2
                data_inicial = refs[1]  # A2
                
                # Busca as datas no banco
                cursor.execute("""
                    SELECT str_element 
                    FROM forms_tab 
                    WHERE name_element = ? AND user_id = ?
                """, (data_final, st.session_state.user_id))
                result = cursor.fetchone()
                data_final_str = result[0] if result and result[0] else None
                
                cursor.execute("""
                    SELECT str_element 
                    FROM forms_tab 
                    WHERE name_element = ? AND user_id = ?
                """, (data_inicial, st.session_state.user_id))
                result = cursor.fetchone()
                data_inicial_str = result[0] if result and result[0] else None
                
                # Converte as datas para dias
                dias_final = date_to_days(data_final_str)
                dias_inicial = date_to_days(data_inicial_str)
                
                # Calcula a diferença em dias
                diff_dias = dias_final - dias_inicial
                
                # Converte para meses (usando média mais precisa de dias por mês)
                meses = diff_dias / 30.44
                
                return max(0, meses)  # Garante que não retorne valor negativo
        
        # Processa cada referência na fórmula
        cell_refs = re.findall(r'(?:Insumos!)?[A-Z][0-9]+', processed_formula)
        
        for ref in cell_refs:
            float_value = get_element_value(
                cursor, 
                ref, 
                st.session_state.user_id if not ref.startswith('Insumos!') else None
            )
            processed_formula = re.sub(r'\b' + re.escape(ref) + r'\b', str(float_value), processed_formula)
        
        result = eval(processed_formula)
        return float(result)
        
    except Exception as e:
        st.error(f"Erro no cálculo da fórmula: {str(e)}")
        return 0.0

def process_conditional_element(cursor, element):
    """
    Processa elemento do tipo 'condicao' seguindo a lógica especificada.
    """
    try:
        name = element[0]
        math_ref = element[2]
        select_pairs = element[5]
        
        cursor.execute("""
            SELECT str_element 
            FROM forms_tab 
            WHERE name_element = ? AND user_id = ?
        """, (math_ref, st.session_state.user_id))
        
        ref_result = cursor.fetchone()
        if not ref_result or not ref_result[0]:
            return 0.0
            
        selected_value = ref_result[0].strip()
        pairs = [pair.strip() for pair in select_pairs.split('|')]
        
        for pair in pairs:
            condition, target = pair.split(':')
            condition = condition.strip()
            target = target.strip()
            
            if condition == selected_value:
                cursor.execute("""
                    SELECT math_element 
                    FROM forms_insumos 
                    WHERE name_element = ?
                """, (target,))
                
                result = cursor.fetchone()
                if result and result[0]:
                    try:
                        math_value = result[0]
                        if '/' in math_value:
                            num, den = map(float, math_value.split('/'))
                            final_value = num / den
                        else:
                            final_value = float(math_value)
                        
                        cursor.execute("""
                            UPDATE forms_tab 
                            SET value_element = ? 
                            WHERE name_element = ? AND user_id = ?
                        """, (final_value, name, st.session_state.user_id))
                        
                        return final_value
                        
                    except ValueError:
                        return 0.0
                    
        return 0.0
        
    except Exception as e:
        st.error(f"Erro ao processar condição: {str(e)}")
        return 0.0

def titulo(cursor, element):
    """
    Exibe títulos formatados na interface com base nos valores do banco de dados.
    """
    try:
        name, msg, col, row, str_value = element[0], element[3], element[7], element[8], element[6]
        type_elem = element[1]  # type_element
        
        # Verifica se a coluna é válida
        if col > 6:
            st.error(f"Posição de coluna inválida para o título {name}: {col}. Deve ser entre 1 e 6.")
            return
        
        # Se for do tipo 'titulo', usa o str_element do próprio registro
        if type_elem == 'titulo':
            if str_value:
                formatted_msg = f"{str_value.replace('✅ Operação concluída com sucesso!', msg)}"
                st.markdown(formatted_msg, unsafe_allow_html=True)
                return
        
        # Para os demais casos
        if str_value and not "Operação concluída" in str_value:
            st.markdown(str_value, unsafe_allow_html=True)
            st.markdown(msg, unsafe_allow_html=True)
        else:
            st.markdown(msg, unsafe_allow_html=True)
                
    except Exception as e:
        st.error(f"Erro ao processar título: {str(e)}")

def new_user(cursor, user_id):
    """
    Inicializa registros para um novo usuário copiando dados do user_id 0.
    """
    try:
        # Verifica se já existem registros para o usuário
        cursor.execute("""
            SELECT COUNT(*) FROM forms_tab WHERE user_id = ?
        """, (user_id,))
        
        if cursor.fetchone()[0] > 0:
            return  # Usuário já tem registros
            
        # Copia apenas os registros da forms_tab do user_id 0
        cursor.execute("""
            INSERT INTO forms_tab (
                name_element, type_element, math_element, msg_element,
                value_element, select_element, str_element, e_col, e_row,
                user_id
            )
            SELECT 
                name_element, type_element, math_element, msg_element,
                value_element, select_element, str_element, e_col, e_row,
                ? as user_id
            FROM forms_tab 
            WHERE user_id = 0
        """, (user_id,))
        
        st.success(f"Registros iniciais criados para o usuário {user_id}")
        
    except Exception as e:
        st.error(f"Erro ao criar registros para novo usuário: {str(e)}")
        raise

def process_forms_tab():
    """Processa registros da tabela forms_tab e exibe em layout de grade."""
    conn = None
    try:
        # Verifica se há um usuário logado
        if 'user_id' not in st.session_state:
            st.error("Usuário não está logado!")
            return
            
        user_id = st.session_state.user_id
        
        # Títulos com estilo
        # st.title("Estimativas Anuais de Perfil Ambiental")
        st.markdown("## Página de Entrada de Dados - Tipo do Café")
        
        # Inicializa session_state
        if 'form_values' not in st.session_state:
            st.session_state.form_values = {}
        
        # Conexão com o banco
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # Inicializa registros para novo usuário se necessário
        new_user(cursor, user_id)
        conn.commit()

        # Busca elementos ordenados (modificada para incluir user_id)
        cursor.execute("""
            SELECT name_element, type_element, math_element, msg_element,
                   value_element, select_element, str_element, e_col, e_row
            FROM forms_tab
            WHERE user_id = ?
            ORDER BY e_row, e_col
        """, (user_id,))
        elements = cursor.fetchall()

        # Agrupa elementos por linha
        rows = {}
        for element in elements:
            e_row = element[8]
            if e_row not in rows:
                rows[e_row] = []
            rows[e_row].append(element)

        # Processa cada linha
        for row_num in sorted(rows.keys()):
            row_elements = rows[row_num]
            
            # Verifica se é uma linha de espaçamento - type element = pula_linha
            if any(element[1] == 'pula_linha' for element in row_elements):
                st.markdown("<br>", unsafe_allow_html=True)
                continue
            
            # Layout com 6 colunas
            cols = st.columns(6)
            
            for element in row_elements:
                name = element[0]
                type_elem = element[1]
                math_elem = element[2]
                msg = element[3]
                value = element[4]
                select_options = element[5]
                str_value = element[6]
                e_col = element[7] - 1  # Ajusta para índice 0-5
                
                # Verifica se o índice da coluna está dentro do limite
                if e_col >= 6:
                    st.error(f"Coluna inválida para o elemento {name}: {e_col + 1}. Deve ser entre 1 e 6.")
                    continue

                with cols[e_col]:
                    try:
                        # Processa elementos do tipo título
                        if type_elem == 'titulo':
                            titulo(cursor, element)
                            continue

                        # Processa elementos ocultos
                        if type_elem.endswith('H'):
                            if type_elem == 'formulaH':
                                result = calculate_formula(math_elem, st.session_state.form_values, cursor)
                                cursor.execute("""
                                    UPDATE forms_tab 
                                    SET value_element = ? 
                                    WHERE name_element = ? AND user_id = ?
                                """, (result, name, st.session_state.user_id))
                                conn.commit()
                            elif type_elem == 'condicaoH':
                                result = process_conditional_element(cursor, element)
                            continue

                        # Processamento normal para elementos visíveis
                        if type_elem == 'selectbox':
                            options = [opt.strip() for opt in select_options.split('|')]
                            selected = st.selectbox(
                                msg,
                                options=options,
                                key=f"select_{name}_{row_num}_{e_col}",
                                index=options.index(str_value) if str_value in options else 0
                            )
                            
                            if selected != str_value:
                                cursor.execute("""
                                    UPDATE forms_tab 
                                    SET str_element = ? 
                                    WHERE name_element = ? AND user_id = ?
                                """, (selected, name, st.session_state.user_id))
                                conn.commit()
                                st.rerun()
                            
                            st.session_state.form_values[name] = 0.0

                        elif type_elem == 'call_insumos':
                            try:
                                result = call_insumos(cursor, element)
                                conn.commit()
                                
                                # Configurações de estilo para métricas
                                FONT_SIZES = {
                                    'small': '12px',
                                    'medium': '16px',
                                    'large': '20px',
                                    'xlarge': '24px'
                                }
                                
                                msg_parts = msg.split('|')
                                display_msg = msg_parts[0].strip()
                                font_size = 'medium'
                                
                                if len(msg_parts) > 1:
                                    for param in msg_parts[1:]:
                                        if param.startswith('size:'):
                                            requested_size = param.split(':')[1].strip()
                                            if requested_size in FONT_SIZES:
                                                font_size = requested_size

                                st.markdown(f"""
                                    <div style='text-align: left;'>
                                        <p style='font-size: {FONT_SIZES[font_size]}; margin-bottom: 0;'>{display_msg}</p>
                                        <p style='font-size: {FONT_SIZES[font_size]}; font-weight: bold;'>{result:.2f}</p>
                                    </div>
                                    """, 
                                    unsafe_allow_html=True
                                )
                            except Exception as e:
                                st.error(f"Erro ao processar call_insumos: {str(e)}")

                        elif type_elem == 'input':
                            try:
                                # Trata o valor atual sempre com 2 casas decimais na exibição
                                if value is not None:
                                    try:
                                        # Formata o número sempre com 2 casas decimais
                                        current_value = f"{float(value):.2f}"
                                    except:
                                        current_value = "0.00"
                                else:
                                    current_value = "0.00"
                                
                                input_value = st.text_input(
                                    msg,
                                    value=current_value,
                                    key=f"input_{name}_{row_num}_{e_col}"
                                )
                                
                                try:
                                    cleaned_input = input_value.strip().replace(',', '.')
                                    numeric_value = float(cleaned_input) if cleaned_input else 0.0
                                    st.session_state.form_values[name] = numeric_value
                                    
                                    if abs(numeric_value - (float(value) if value is not None else 0)) > 1e-10:
                                        cursor.execute("""
                                            UPDATE forms_tab 
                                            SET value_element = ? 
                                            WHERE name_element = ? AND user_id = ?
                                        """, (numeric_value, name, st.session_state.user_id))
                                        conn.commit()
                                        st.rerun()
                                    
                                except ValueError:
                                    st.error(f"Por favor, insira apenas números em {msg}")
                                    numeric_value = float(value) if value is not None else 0.0
                                    st.session_state.form_values[name] = numeric_value
                            
                            except Exception as e:
                                st.error(f"Erro ao processar input: {str(e)}")

                        elif type_elem == 'formula':
                            try:
                                # Configurações de estilo para métricas
                                FONT_SIZES = {
                                    'small': '12px',
                                    'medium': '16px',
                                    'large': '20px',
                                    'xlarge': '24px'
                                }
                                
                                msg_parts = msg.split('|')
                                display_msg = msg_parts[0].strip()
                                font_size = 'medium'
                                
                                if len(msg_parts) > 1:
                                    for param in msg_parts[1:]:
                                        if param.startswith('size:'):
                                            requested_size = param.split(':')[1].strip()
                                            if requested_size in FONT_SIZES:
                                                font_size = requested_size

                                result = calculate_formula(math_elem, st.session_state.form_values, cursor)
                                
                                cursor.execute("""
                                    UPDATE forms_tab 
                                    SET value_element = ? 
                                    WHERE name_element = ? AND user_id = ?
                                """, (result, name, st.session_state.user_id))
                                conn.commit()
                                
                                st.markdown(f"""
                                    <div style='text-align: left;'>
                                        <p style='font-size: {FONT_SIZES[font_size]}; margin-bottom: 0;'>{display_msg}</p>
                                        <p style='font-size: {FONT_SIZES[font_size]}; font-weight: bold;'>{result:.2f}</p>
                                    </div>
                                    """, 
                                    unsafe_allow_html=True
                                )

                            except Exception as e:
                                st.error(f"Erro ao processar fórmula: {str(e)}")

                        elif type_elem == 'condicao':
                            try:
                                # Configurações de estilo para métricas
                                FONT_SIZES = {
                                    'small': '12px',    # Fonte pequena
                                    'medium': '16px',   # Fonte média (padrão)
                                    'large': '20px',    # Fonte grande
                                    'xlarge': '24px'    # Fonte extra grande
                                }
                                
                                # Extrai o tamanho da fonte do msg_element (se existir)
                                # Formato esperado: "texto|size:small" ou apenas "texto"
                                msg_parts = msg.split('|')
                                display_msg = msg_parts[0].strip()
                                font_size = 'medium'  # Tamanho padrão
                                
                                # Processa parâmetros adicionais
                                if len(msg_parts) > 1:
                                    for param in msg_parts[1:]:
                                        if param.startswith('size:'):
                                            requested_size = param.split(':')[1].strip()
                                            if requested_size in FONT_SIZES:
                                                font_size = requested_size

                                # Processa o elemento condicional
                                result = process_conditional_element(cursor, element)
                                
                                # Aplica estilo customizado usando HTML/CSS
                                st.markdown(f"""
                                    <div style='text-align: center;'>
                                        <p style='font-size: {FONT_SIZES[font_size]}; margin-bottom: 0;'>{display_msg}</p>
                                        <p style='font-size: {FONT_SIZES[font_size]}; font-weight: bold;'>{result:.2f}</p>
                                    </div>
                                    """, 
                                    unsafe_allow_html=True
                                )

                            except Exception as e:
                                st.error(f"Erro ao processar condição: {str(e)}")

                        elif type_elem == 'input_data':
                            # Pega o valor atual do str_element
                            current_value = str_value if str_value else ''
                            
                            # Campo de entrada para data
                            input_value = st.text_input(
                                msg,
                                value=current_value,
                                key=f"input_data_{name}_{row_num}_{e_col}"
                            )
                            
                            # Validação do formato da data
                            if input_value:
                                # Regex para validar formato dd/mm/aaaa
                                date_pattern = r'^\d{2}/\d{2}/\d{4}$'
                                if not re.match(date_pattern, input_value):
                                    st.error(f"Por favor, insira a data no formato dd/mm/aaaa em {msg}")
                                else:
                                    # Validação adicional dos valores da data
                                    try:
                                        dia, mes, ano = map(int, input_value.split('/'))
                                        # Verifica se é uma data válida
                                        if (mes < 1 or mes > 12 or dia < 1 or dia > 31 or
                                            ano < 1900 or ano > 2100 or
                                            (mes in [4, 6, 9, 11] and dia > 30) or
                                            (mes == 2 and dia > 29)):
                                            st.error(f"Data inválida em {msg}")
                                        else:
                                            # Atualiza o banco apenas se o valor mudou
                                            if input_value != current_value:
                                                cursor.execute("""
                                                    UPDATE forms_tab 
                                                    SET str_element = ? 
                                                    WHERE name_element = ? AND user_id = ?
                                                """, (input_value, name, st.session_state.user_id))
                                                conn.commit()
                                                st.rerun()
                                    except ValueError:
                                        st.error(f"Data inválida em {msg}")
                            
                            # Mantém o value_element como 0 já que não é usado para datas
                            st.session_state.form_values[name] = '0.0'

                        elif type_elem == 'formula_data':
                            try:
                                # Configurações de estilo para métricas
                                FONT_SIZES = {
                                    'small': '12px',    # Fonte pequena
                                    'medium': '16px',   # Fonte média (padrão)
                                    'large': '20px',    # Fonte grande
                                    'xlarge': '24px'    # Fonte extra grande
                                }
                                
                                # Extrai o tamanho da fonte do msg_element (se existir)
                                msg_parts = msg.split('|')
                                display_msg = msg_parts[0].strip()
                                font_size = 'medium'  # Tamanho padrão
                                
                                # Processa parâmetros adicionais
                                if len(msg_parts) > 1:
                                    for param in msg_parts[1:]:
                                        if param.startswith('size:'):
                                            requested_size = param.split(':')[1].strip()
                                            if requested_size in FONT_SIZES:
                                                font_size = requested_size

                                # Calcula o resultado da fórmula de data
                                result = calculate_formula(math_elem, st.session_state.form_values, cursor)
                                
                                # Atualiza o value_element no banco
                                cursor.execute("""
                                    UPDATE forms_tab 
                                    SET value_element = ? 
                                    WHERE name_element = ? AND user_id = ?
                                """, (result, name, st.session_state.user_id))
                                conn.commit()
                                
                                # Aplica estilo customizado usando HTML/CSS
                                st.markdown(f"""
                                    <div style='text-align: left;'>
                                        <p style='font-size: {FONT_SIZES[font_size]}; margin-bottom: 0;'>{display_msg}</p>
                                        <p style='font-size: {FONT_SIZES[font_size]}; font-weight: bold;'>{result:.1f} meses</p>
                                    </div>
                                    """, 
                                    unsafe_allow_html=True
                                )

                            except Exception as e:
                                st.error(f"Erro ao processar fórmula de data: {str(e)}")

                    except Exception as e:
                        st.error(f"Erro ao processar {name}: {str(e)}")

        # Separador
        st.divider()
        
        # Lista de registros ADM
        with st.expander("Lista de Registros ADM"):
            if st.button("Atualizar Dados"):
                st.rerun()

            table_choice = st.selectbox(
                "Selecione a tabela:",
                ["forms_tab", "forms_insumos", "resultados_tab"],
                key="table_selector"
            )

            # Buscar dados com base na tabela selecionada
            if table_choice == "forms_tab":
                cursor.execute("""
                    SELECT ID_element, name_element, type_element, math_element, msg_element,
                           value_element, select_element, str_element, e_col, e_row, user_id
                    FROM forms_tab
                    ORDER BY user_id, e_row, e_col
                """)
                columns = [
                    'ID_element', 'name_element', 'type_element', 'math_element', 'msg_element',
                    'value_element', 'select_element', 'str_element', 'e_col', 'e_row', 'user_id'
                ]
            elif table_choice == "resultados_tab":
                cursor.execute("""
                    SELECT ID_element, name_element, type_element, math_element, msg_element,
                           value_element, select_element, str_element, e_col, e_row, user_id
                    FROM resultados_tab
                    ORDER BY user_id, e_row, e_col
                """)
                columns = [
                    'ID_element', 'name_element', 'type_element', 'math_element', 'msg_element',
                    'value_element', 'select_element', 'str_element', 'e_col', 'e_row', 'user_id'
                ]
            else:  # forms_insumos
                cursor.execute("""
                    SELECT ID_element, name_element, type_element, math_element, msg_element,
                           value_element, select_element, str_element, e_col, e_row
                    FROM forms_insumos
                    ORDER BY e_row, e_col
                """)
                columns = [
                    'ID_element', 'name_element', 'type_element', 'math_element', 'msg_element',
                    'value_element', 'select_element', 'str_element', 'e_col', 'e_row'
                ]

            elements = cursor.fetchall()

            # Criar DataFrame
            df = pd.DataFrame(elements, columns=columns)
            
            # Formata mantendo as casas decimais originais do número e usando vírgula como separador decimal
            def format_value(x):
                try:
                    if x is None:
                        return "0"
                    # Converte para float primeiro para garantir que é um número
                    num = float(x)
                    # Converte para string mantendo apenas as casas decimais significativas
                    str_num = f"{num}"
                    # Remove zeros à direita após o ponto decimal, mas mantém um zero se for número inteiro
                    if '.' in str_num:
                        str_num = str_num.rstrip('0').rstrip('.')
                    # Substitui ponto por vírgula para padrão BR
                    str_num = str_num.replace('.', ',')
                    return str_num
                except:
                    return str(x) if x else "0"
                    
            df['value_element'] = df['value_element'].apply(format_value)

            # Mostrar DataFrame
            st.dataframe(df)
            
            # Botão para download em TXT
            if not df.empty:
                txt_data = df.to_csv(sep='\t', index=False, encoding='cp1252')
                st.download_button(
                    label="Download TXT",
                    data=txt_data,
                    file_name=f"{table_choice}.txt",
                    mime="text/plain"
                )

    except Exception as e:
        st.error(f"Erro ao processar formulário: {str(e)}")
    finally:
        if conn:
            conn.close()

def call_insumos(cursor, element):
    """
    Busca valor de referência na tabela forms_insumos e atualiza value_element.
    
    Args:
        cursor: Cursor do banco de dados SQLite
        element: Tupla contendo os dados do elemento (name, type, math, msg, value, select, str, col, row)
    
    Returns:
        float: Valor numérico encontrado ou 0.0 em caso de erro
    """
    try:
        name = element[0]  # name_element da forms_tab
        str_value = element[6]  # str_element da forms_tab (ex: 'InsumosI15')
        
        # Verifica se há uma referência válida
        if not str_value:
            return 0.0
            
        # Busca o math_element na forms_insumos onde name_element = str_value da forms_tab
        cursor.execute("""
            SELECT math_element 
            FROM forms_insumos 
            WHERE name_element = ?
        """, (str_value.strip(),))
        
        result = cursor.fetchone()
        if not result:
            st.warning(f"Referência '{str_value}' não encontrada em forms_insumos")
            return 0.0
            
        try:
            math_value = result[0]
            if not math_value:
                return 0.0
                
            # Processa o valor do math_element
            if '/' in math_value:  # Se for uma fração
                num, den = map(float, math_value.split('/'))
                if den == 0:
                    st.error(f"Divisão por zero encontrada em '{math_value}'")
                    return 0.0
                final_value = num / den
            else:
                final_value = float(math_value)
            
            # Atualiza o valor no banco como REAL
            cursor.execute("""
                UPDATE forms_tab 
                SET value_element = CAST(? AS REAL)
                WHERE name_element = ? AND user_id = ?
            """, (final_value, name, st.session_state.user_id))
            
            return final_value
            
        except ValueError as e:
            st.error(f"Valor inválido '{result[0]}' para a referência '{str_value}': {str(e)}")
            return 0.0
            
    except sqlite3.Error as e:
        st.error(f"Erro no banco de dados: {str(e)}")
        return 0.0
    except Exception as e:
        st.error(f"Erro inesperado ao processar referência: {str(e)}")
        return 0.0
