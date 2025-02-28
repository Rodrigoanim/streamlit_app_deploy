# Arquivo: form_model.py
# type formula font attribute - somente inteiros
# 27/02/2025 - 11:00 - alterado para calcular o valor do insumo sem usr a tabela forms_insumos

import sqlite3
import streamlit as st
import pandas as pd
import re
# import logging

from config import DB_PATH
from paginas.monitor import registrar_acesso  # Ajustado para incluir o caminho completo

MAX_COLUMNS = 5  # Número máximo de colunas no layout


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
    if result and result[0] is not None:
        return float(result[0])  # Valor já está como REAL no banco
    return 0.0

def calculate_formula(formula, values, cursor):
    """
    Calcula o resultado de uma fórmula com suporte a operações matemáticas e datas.
    """
    try:
        # Se a fórmula for um número direto
        if isinstance(formula, (int, float)):
            return float(formula)
        
        # Se for string numérica
        if isinstance(formula, str):
            formula = formula.replace(',', '.')
            if formula.replace('.','',1).isdigit():
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
        
        # Processa referências na fórmula
        cell_refs = re.findall(r'(?:Insumos!)?[A-Z]{1,2}[0-9]+', processed_formula)
        
        for ref in cell_refs:
            float_value = get_element_value(
                cursor, 
                ref, 
                st.session_state.user_id if not ref.startswith('Insumos!') else None
            )
            processed_formula = re.sub(r'\b' + re.escape(ref) + r'\b', str(float_value), processed_formula)
        
        # Substitui vírgulas por pontos antes do eval
        processed_formula = processed_formula.replace(',', '.')
        
        # Verifica divisão por zero antes do eval
        # Primeiro, avalia a expressão para obter os denominadores
        def safe_div(x, y):
            if abs(float(y)) < 1e-10:  # Considera valores muito próximos de zero
                return 0.0
            return x / y
        
        # Cria um ambiente seguro para eval com a função de divisão segura
        safe_env = {
            'safe_div': safe_div,
            '__builtins__': None
        }
        
        # Substitui todas as divisões pela função segura
        processed_formula = re.sub(r'(\d+\.?\d*|\([^)]+\))\s*/\s*(\d+\.?\d*|\([^)]+\))', r'safe_div(\1, \2)', processed_formula)
        
        result = float(eval(processed_formula, safe_env, {}))
        return result
        
    except Exception as e:
        if "division by zero" in str(e):
            return 0.0  # Retorna 0 silenciosamente em caso de divisão por zero
        st.error(f"Erro no cálculo da fórmula: {str(e)}")
        return 0.0

def condicaoH(cursor, element, conn):
    """
    Atualiza o value_element baseado em um valor de referência e mapeamento.
    """
    # print(f"\nCondicaoH chamada para elemento: {element[0]}")  # Debug
    
    try:
        # Extrai informações da linha atual
        name_element = element[1]  # D151, D152, etc
        math_ref = element[3]      # D15 (vem da coluna math_element)
        select_options = element[6] # String com mapeamento (vem da coluna str_element)
        
        # print(f"  math_ref: {math_ref}")  # Debug
        # print(f"  select_options: {select_options}")  # Debug
        
        # 1. Validações iniciais
        if not all([name_element, math_ref, select_options]):
            # print("  Erro: dados incompletos")  # Debug
            return False
            
        # 2. Busca str_element da referência
        cursor.execute("""
            SELECT str_element 
            FROM forms_tab 
            WHERE name_element = ? AND user_id = ?
        """, (math_ref, st.session_state.user_id))
        
        result = cursor.fetchone()
        if not result or result[0] is None:
            # print("  Erro: str_element não encontrado")  # Debug
            return False
            
        str_ref = result[0].strip()  # Remove espaços extras
        # print(f"  str_ref encontrado: {str_ref}")  # Debug
        
        # 3. Processa mapeamento do select_options
        try:
            # Remove aspas duplas do início e fim do select_options
            select_options = select_options.strip('"')
            
            # Divide os pares de valores
            mapeamento = {}
            for par in select_options.split('|'):
                if ':' in par:
                    chave, valor = par.split(':')
                    chave = chave.strip()  # Remove espaços extras da chave
                    valor = valor.strip()  # Remove espaços extras do valor
                    mapeamento[chave] = float(valor)
            
            # print(f"  Mapeamento: {mapeamento}")  # Debug
            
            # Busca valor correspondente
            if str_ref in mapeamento:
                valor_encontrado = mapeamento[str_ref]
                # print(f"  Valor encontrado: {valor_encontrado}")  # Debug
                
                # 4. Atualiza o banco
                cursor.execute("""
                    UPDATE forms_tab 
                    SET value_element = ?
                    WHERE name_element = ? AND user_id = ?
                """, (valor_encontrado, name_element, st.session_state.user_id))
                
                conn.commit()
                return True
            
            # print(f"  Erro: str_ref '{str_ref}' não encontrado no mapeamento")  # Debug
            return False
            
        except ValueError:
            # print("  Erro: ValueError ao processar valores")  # Debug
            return False
            
        except sqlite3.Error:
            # print("  Erro: Erro no banco de dados")  # Debug
            conn.rollback()
            return False
        
    except Exception as e:
        # print(f"  Erro inesperado: {str(e)}")  # Debug
        if 'conn' in locals():
            conn.rollback()
        return False

def titulo(cursor, element):
    """
    Exibe títulos formatados na interface com base nos valores do banco de dados.
    """
    try:
        name = element[0]
        type_elem = element[1]
        msg = element[3].strip("'").strip('"')  # Remove aspas simples e duplas
        str_value = element[6].strip("'").strip('"') if element[6] else ''  # Remove aspas simples e duplas
        
        # Se for do tipo 'titulo', usa o str_element do próprio registro
        if type_elem == 'titulo':
            if str_value:
                formatted_msg = str_value.replace('✅ Operação concluída com sucesso!', msg)
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
        
        if cursor.fetchone()[0] == 0:  # Se não existem registros
            # Copia todos os dados do user_id 0
            cursor.execute("""
                INSERT INTO forms_tab (
                    name_element, type_element, math_element, msg_element,
                    value_element, select_element, str_element, e_col, e_row,
                    section, col_len, user_id
                )
                SELECT 
                    name_element, type_element, math_element, msg_element,
                    value_element, select_element, str_element, e_col, e_row,
                    section, col_len, ? as user_id
                FROM forms_tab 
                WHERE user_id = 0
            """, (user_id,))
            
            st.success(f"Registros iniciais criados para o usuário {user_id}")
        
    except Exception as e:
        st.error(f"Erro ao criar registros para novo usuário: {str(e)}")
        raise

def process_forms_tab(section='cafe'):
    """
    Processa registros da tabela forms_tab e exibe em layout de grade.
    
    Args:
        section (str): Seção a ser exibida ('cafe', 'moagem' ou 'embalagem')
    """
    conn = None
    try:
        # Inicializa flag de log no session_state se não existir
        log_key = f"log_registered_{section}"
        if log_key not in st.session_state:
            st.session_state[log_key] = False
            
        # 1. Verifica se há um usuário logado
        if 'user_id' not in st.session_state:
            st.error("Usuário não está logado!")
            return
            
        # 2. Armazena user_id em variável
        user_id = st.session_state.user_id
        
        # Títulos com estilo baseados na seção
        titles = {
            'cafe': "Entrada de Dados - Café",
            'moagem': "Entrada de Dados - Torrefação e Moagem",
            'embalagem': "Entrada de Dados - Embalagem"
        }
        
        title_text = titles.get(section, "Página de Entrada de Dados")
        st.markdown(f"""
            <p style='
                text-align: left;
                font-size: 28px;
                font-weight: bold;
                color: #1E1E1E;
                margin: 15px 0;
                padding: 10px;
                background-color: #FFFFFF;
                border-radius: 5px;
            '>{title_text}</p>
        """, unsafe_allow_html=True)
        
        # Inicializa session_state
        if 'form_values' not in st.session_state:
            st.session_state.form_values = {}
        
        # Conexão com o banco
        conn = sqlite3.connect(DB_PATH)  # Atualizado para usar DB_PATH
        cursor = conn.cursor()

        # 3. Garante que existam dados para o usuário
        new_user(cursor, user_id)
        conn.commit()

        # 4. Busca dados específicos do usuário logado e da seção atual
        cursor.execute("""
            SELECT name_element, type_element, math_element, msg_element,
                   value_element, select_element, str_element, e_col, e_row,
                   col_len
            FROM forms_tab
            WHERE user_id = ? AND section = ?
            ORDER BY e_row, e_col
        """, (user_id, section))
        elements = cursor.fetchall()

        # Verifica se existem elementos para esta seção
        if not elements:
            st.warning(f"Nenhum elemento encontrado para a seção {section}")
            return

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
            
            # Filtra elementos visíveis
            visible_elements = [e for e in row_elements if not e[1].endswith('H')]
            if not visible_elements:
                continue
                
            # Verifica se é uma linha de espaçamento
            if any(element[1] == 'pula_linha' for element in visible_elements):
                st.markdown("<br>", unsafe_allow_html=True)
                continue
            
            # Caso especial: título verde ocupando toda a largura
            if len(visible_elements) == 1 and visible_elements[0][1] == 'titulo':
                element = visible_elements[0]
                msg = element[3]
                col_len = int(element[9]) if element[9] is not None else 1
                
                if 'background-color:#006400' in msg:
                    # Cria colunas mantendo a proporção dentro do MAX_COLUMNS
                    widths = [1] * MAX_COLUMNS  # Lista com 5 colunas de largura 1
                    widths[0] = col_len  # Primeira coluna com largura col_len
                    widths[col_len:] = [0] * (MAX_COLUMNS - col_len)  # Zera as colunas não usadas
                    
                    cols = st.columns(widths)
                    with cols[0]:
                        st.markdown(msg, unsafe_allow_html=True)
                    continue
            
            # Para os elementos normais
            # Calcula o total de colunas necessário baseado em col_len
            total_cols = 0
            for element in visible_elements:
                col_len = int(element[9]) if element[9] is not None else 1
                total_cols += col_len

            # Cria lista de larguras relativas respeitando MAX_COLUMNS
            column_widths = []
            remaining_cols = MAX_COLUMNS

            for element in visible_elements:
                col_len = int(element[9]) if element[9] is not None else 1
                # Ajusta a largura para não ultrapassar o espaço restante
                actual_width = min(col_len, remaining_cols)
                column_widths.append(actual_width)
                remaining_cols -= actual_width

            # Adiciona colunas vazias se necessário
            if remaining_cols > 0:
                column_widths.append(remaining_cols)

            # Cria todas as colunas de uma vez com suas larguras relativas
            cols = st.columns(column_widths)
            
            # Processa os elementos dentro das colunas
            for idx, element in enumerate(visible_elements):
                with cols[idx]:
                    name = element[0]
                    type_elem = element[1]
                    math_elem = element[2]
                    msg = element[3]
                    value = element[4]
                    select_options = element[5]
                    str_value = element[6]
                    e_col = element[7] - 1  # Ajusta para índice 0-4
                    
                    # Verifica se a coluna está dentro do limite
                    if e_col >= MAX_COLUMNS:
                        continue  # Pula silenciosamente elementos fora do limite

                    try:
                        # Processa elementos do tipo título
                        if type_elem == 'titulo':
                            titulo(cursor, element)
                            continue

                        # Processa elementos ocultos
                        if type_elem.endswith('H'):
                            try:
                                if type_elem == 'formulaH':
                                    result = calculate_formula(math_elem, st.session_state.form_values, cursor)
                                elif type_elem == 'condicaoH':
                                    result = condicaoH(cursor, element, conn)
                                elif type_elem == 'call_insumosH':
                                    result = call_insumos(cursor, element)

                                # Atualiza o banco com o resultado
                                if type_elem in ['formulaH', 'condicaoH', 'call_insumosH']:
                                    cursor.execute("""
                                        UPDATE forms_tab 
                                        SET value_element = ? 
                                        WHERE name_element = ? AND user_id = ?
                                    """, (result, name, st.session_state.user_id))
                                    conn.commit()
                                continue

                            except Exception as e:
                                st.error(f"Falha ao processar elemento oculto {name}: {str(e)}")

                        # Processamento normal para elementos visíveis - Selectbox
                        if type_elem == 'selectbox':
                            try:
                                # Validação das opções do select
                                if not select_options:
                                    st.error(f"Erro: Opções vazias para {name}")
                                    continue
                                
                                options = [opt.strip() for opt in select_options.split('|')]
                                display_msg = msg if msg.strip() else name
                                initial_index = options.index(str_value) if str_value in options else 0
                                
                                # Renderiza o selectbox
                                selected = st.selectbox(
                                    display_msg,
                                    options=options,
                                    key=f"select_{name}_{row_num}_{e_col}",
                                    index=initial_index,
                                    label_visibility="collapsed" if not msg.strip() else "visible"
                                )
                                
                                # Se o valor mudou, atualiza os elementos dependentes
                                if selected != str_value:
                                    try:
                                        # Atualiza o próprio selectbox
                                        cursor.execute("""
                                            UPDATE forms_tab 
                                            SET str_element = ?,
                                                value_element = ?
                                            WHERE name_element = ? 
                                            AND user_id = ? 
                                            AND section = ?
                                        """, (selected, 0.0, name, st.session_state.user_id, section))
                                        
                                        # Busca elementos condicaoH que dependem deste selectbox
                                        cursor.execute("""
                                            SELECT * FROM forms_tab 
                                            WHERE type_element = 'condicaoH' 
                                            AND math_element = ? 
                                            AND user_id = ?
                                        """, (name, st.session_state.user_id))
                                        
                                        # Para cada elemento encontrado, chama condicaoH
                                        for elemento in cursor.fetchall():
                                            # print(f"Elemento encontrado: {elemento}")  # Debug adicional
                                            condicaoH(cursor, elemento, conn)
                                        
                                        conn.commit()
                                    
                                    except sqlite3.Error as e:
                                        st.error(f"Erro no banco de dados: {str(e)}")
                                        conn.rollback()

                            except Exception as e:
                                st.error(f"Erro no selectbox {name}: {str(e)}")
                                if 'conn' in locals():
                                    conn.rollback()

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
                                # Converte o valor REAL do banco para exibição no formato BR
                                if value is not None:
                                    current_value = f"{float(value):.2f}".replace('.', ',')
                                else:
                                    current_value = "0,00"
                                
                                # Usa o nome do elemento como label se msg estiver vazio
                                display_msg = msg if msg.strip() else name
                                input_value = st.text_input(
                                    display_msg,
                                    value=current_value,
                                    key=f"input_{name}_{row_num}_{e_col}",
                                    label_visibility="collapsed" if not msg.strip() else "visible"
                                )
                                
                                try:
                                    # Remove pontos de milhar e converte vírgula para ponto
                                    cleaned_input = input_value.strip().replace('.', '').replace(',', '.')
                                    numeric_value = float(cleaned_input)
                                    
                                    # Compara valores como float
                                    if abs(numeric_value - float(value or 0)) > 1e-10:
                                        # Registra log apenas uma vez por seção
                                        if not st.session_state[log_key]:
                                            registrar_acesso(
                                                st.session_state.user_id,
                                                f"forms_{section}",
                                                f"Alteração em formulário de {section}"
                                            )
                                            st.session_state[log_key] = True
                                            
                                        cursor.execute("""
                                            UPDATE forms_tab 
                                            SET value_element = ? 
                                            WHERE name_element = ? AND user_id = ?
                                        """, (numeric_value, name, st.session_state.user_id))
                                        conn.commit()
                                        st.rerun()
                                    
                                    st.session_state.form_values[name] = numeric_value
                                    
                                except ValueError:
                                    st.error(f"Por favor, insira apenas números em {msg}")
                                    st.session_state.form_values[name] = float(value or 0)
                            
                            except Exception as e:
                                st.error(f"Erro ao processar input: {str(e)}")

                        elif type_elem == 'formula':
                            try:
                                # Calcula o resultado da fórmula
                                result = calculate_formula(element[2], st.session_state.form_values, cursor)
                                
                                # Formata o resultado baseado no valor
                                if result >= 0:
                                    result_br = f"{result:.0f}".replace('.', ',')  # Sem casas decimais
                                else:
                                    result_br = f"{result:.3f}".replace('.', ',')  # 3 casas decimais
                                
                                # Limpa as aspas do str_value antes de usar
                                str_value = element[6]
                                if str_value:
                                    str_value = str_value.strip('"').strip("'")  # Remove aspas simples e duplas
                                
                                # Limpa as aspas da mensagem também
                                if msg:
                                    msg = msg.strip('"').strip("'")
                                
                                # Se não houver estilo definido, usa o padrão
                                if not str_value:
                                    str_value = '<div style="text-align: left; font-size: 16px; margin-bottom: 0;">[valor]</div>'
                                
                                # Substitui o placeholder pelo valor calculado
                                formatted_html = str_value.replace('[valor]', result_br)
                                
                                # Se houver mensagem de título
                                if msg:
                                    st.markdown(msg, unsafe_allow_html=True)
                                    st.empty()
                                
                                # Limpa o HTML final e renderiza
                                formatted_html = formatted_html.strip()
                                st.markdown(formatted_html, unsafe_allow_html=True)
                                
                                # Atualiza o valor no banco (valor original, sem formatação)
                                cursor.execute("""
                                    UPDATE forms_tab 
                                    SET value_element = ? 
                                    WHERE name_element = ? AND user_id = ?
                                """, (result, name, st.session_state.user_id))
                                
                            except Exception as e:
                                st.error(f"Erro ao processar fórmula: {str(e)}")
                                return 0.0


                        elif type_elem == 'input_data':
                            # Pega o valor atual do str_element
                            current_value = str_value if str_value else ''
                            
                            # Campo de entrada para data
                            input_value = st.text_input(
                                msg,
                                value=current_value,
                                key=f"input_data_{name}_{row_num}_{e_col}",
                                label_visibility="collapsed" if not msg.strip() else "visible"
                            )
                            
                            # Validação do formato da data
                            if input_value:
                                # Regex para validar formato dd/mm/aaaa
                                date_pattern = r'^\d{2}/\d{2}/\d{4}$'
                                if not re.match(date_pattern, input_value):
                                    st.error(f"Por favor, insira a data no formato dd/mm/aaaa em {msg}")
                                else:
                                    try:
                                        dia, mes, ano = map(int, input_value.split('/'))
                                        # Verifica se é uma data válida
                                        if (mes < 1 or mes > 12 or dia < 1 or dia > 31 or
                                            ano < 1900 or ano > 2100 or
                                            (mes in [4, 6, 9, 11] and dia > 30) or
                                            (mes == 2 and dia > 29)):
                                            st.error(f"Data inválida em {msg}")
                                        else:
                                            # Calcula dias desde 01/01/1900
                                            days_since_1900 = date_to_days(input_value)
                                            
                                            # Atualiza o banco apenas se o valor mudou
                                            if input_value != current_value:
                                                cursor.execute("""
                                                    UPDATE forms_tab 
                                                    SET str_element = ?,
                                                        value_element = ? 
                                                    WHERE name_element = ? AND user_id = ?
                                                """, (input_value, days_since_1900, name, st.session_state.user_id))
                                                conn.commit()
                                                st.rerun()
                                            
                                            # Atualiza o form_values com o número de dias
                                            st.session_state.form_values[name] = days_since_1900
                                            
                                    except ValueError:
                                        st.error(f"Data inválida em {msg}")

                        elif type_elem == 'formula_data':
                            # Desabilitado - não faz nada
                            pass

                    except Exception as e:
                        st.error(f"Erro ao processar {name}: {str(e)}")

        # Separador
        st.divider()

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
                num, den = map(lambda x: float(x.replace(',', '.')), math_value.split('/'))
                if den == 0:
                    st.error(f"Divisão por zero encontrada em '{math_value}'")
                    return 0.0
                final_value = num / den
            else:
                final_value = float(math_value.replace(',', '.'))
            
            # Converte para formato BR antes de salvar
            final_value_br = f"{final_value:.2f}".replace('.', ',')
            
            cursor.execute("""
                UPDATE forms_tab 
                SET value_element = ?
                WHERE name_element = ? AND user_id = ?
            """, (final_value_br, name, st.session_state.user_id))
            
            return final_value  # Retorna float para cálculos
            
        except ValueError as e:
            st.error(f"Valor inválido '{result[0]}' para a referência '{str_value}': {str(e)}")
            return 0.0
            
    except sqlite3.Error as e:
        st.error(f"Erro no banco de dados: {str(e)}")
        return 0.0
    except Exception as e:
        st.error(f"Erro inesperado ao processar referência: {str(e)}")
        return 0.0

def formula(cursor, element):
    """
    Exibe elementos do tipo 'formula' com estilos definidos no str_element.
    
    Esta função lida com o timing de renderização do Streamlit para garantir
    que os estilos sejam aplicados corretamente. As pausas estratégicas (st.empty())
    são necessárias devido à natureza assíncrona do Streamlit e como ele processa
    elementos HTML.
    
    Parâmetros:
        cursor: Cursor do banco de dados SQLite
        element: Tupla contendo os dados do elemento (name, type, math, msg, etc.)
    """
    try:
        name = element[0]
        msg = element[3].strip("'").strip('"') if element[3] else ''
        
        # Limpa as aspas extras do str_element
        str_value = element[6]
        if str_value:
            str_value = str_value.strip('"""').strip("'''").strip('"').strip("'")
        
        # Calcula o resultado da fórmula
        result = calculate_formula(element[2], st.session_state.form_values, cursor)
        result_br = f"{result:.2f}".replace('.', ',')
        
        # Se não houver estilo definido, usa o padrão
        if not str_value:
            str_value = '<div style="text-align: left; font-size: 16px; margin-bottom: 0;">[valor]</div>'
        
        # Garante que elementos anteriores foram renderizados
        st.empty()
        
        # Substitui o placeholder pelo valor calculado
        formatted_html = str_value.replace('[valor]', result_br)
        
        # Se houver mensagem de título
        if msg:
            st.markdown(msg, unsafe_allow_html=True)
            st.empty()
        
        # Limpa o HTML final e renderiza
        formatted_html = formatted_html.strip()
        st.markdown(formatted_html, unsafe_allow_html=True)
        
        # Atualiza o valor no banco
        cursor.execute("""
            UPDATE forms_tab 
            SET value_element = ? 
            WHERE name_element = ? AND user_id = ?
        """, (result, name, st.session_state.user_id))
        
    except Exception as e:
        st.error(f"Erro ao processar fórmula: {str(e)}")
        return 0.0
