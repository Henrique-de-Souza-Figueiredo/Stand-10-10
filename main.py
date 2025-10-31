from flask import Flask, render_template, flash, request, url_for, redirect, session
from flask_bcrypt import generate_password_hash, check_password_hash
from datetime import date
import fdb

app = Flask(__name__)

app.config['SECRET_KEY'] = 'senhastandsi,teacademia'

host = 'localhost'
database = r'C:\Users\Aluno\Desktop\Stand-10-10\BANCO.FDB'
user = 'sysdba'
password = 'sysdba'

con = fdb.connect(host=host, database=database, user=user, password=password)


@app.route('/')
def index():
    if 'id_usuario' in session:
        flash('Você precisa deslogar primeiro.', 'erro')
        if session.get('tipo') == 1:
            return redirect('alunodashbord')
        elif session.get('tipo') == 2:
            return redirect('professordashbord')
        else:
            return redirect('dashbordadmin')

    return render_template('index.html', titulo='Pagina inicial')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/cadastro')
def cadastro():
    if 'id_usuario' in session:
        flash('Você precisa deslogar primeiro.', 'erro')
        if session.get('alunodashbord') == 1:
            return redirect('')
        elif session.get('tipo') == 2:
            return redirect('professordashbord')
        else:
            return redirect('dashbordadmin')

    return render_template('cadastro.html', titulo='Novo usuario')


@app.route('/alunodashbord')
def alunodashbord():
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'erro')
        return redirect(url_for('login'))

    if session.get('tipo') != 1:
        flash('Acesso negado. Somente alunos nessa página.', 'erro')
        return redirect(url_for('login'))

    id_aluno = session['id_usuario']

    hoje = date.today()

    dia_semana_hoje = hoje.weekday() + 1

    cursor = con.cursor()
    cursor.execute("""
                   SELECT COUNT(*)
                   FROM (SELECT A.ID_AULA
                         FROM AULA A
                                  LEFT JOIN AULA_ALUNO AA ON A.ID_AULA = AA.ID_AULA
                         WHERE A.DIA_SEMANA = ? -- Alterado
                         GROUP BY A.ID_AULA, A.CAPACIDADE
                         HAVING COUNT(AA.ID_ALUNO) < A.CAPACIDADE) AS sub
                   """, (dia_semana_hoje,))  # Passa o número do dia de hoje
    aulas_disponiveis_hoje = cursor.fetchone()[0]

    cursor.execute("""
                   SELECT COUNT(*)
                   FROM (SELECT A.ID_AULA
                         FROM AULA A
                                  LEFT JOIN AULA_ALUNO AA ON A.ID_AULA = AA.ID_AULA
                         GROUP BY A.ID_AULA, A.CAPACIDADE
                         HAVING COUNT(AA.ID_ALUNO) < A.CAPACIDADE) AS sub
                   """)
    aulas_disponiveis_semana = cursor.fetchone()[0]

    cursor.execute("""
                   SELECT COUNT(*)
                   FROM AULA_ALUNO AA
                            JOIN AULA A ON AA.ID_AULA = A.ID_AULA
                   WHERE AA.ID_ALUNO = ?
                     AND A.DIA_SEMANA = ?
                   """, (id_aluno, dia_semana_hoje))
    aulas_inscritas_hoje = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM AULA_ALUNO AA WHERE AA.ID_ALUNO = ?", (id_aluno,))
    aulas_inscritas_semana = cursor.fetchone()[0]



    cursor.close()

    return render_template('aluno-dashbord.html',titulo='Dashboard Aluno',aulas_disponiveis_hoje=aulas_disponiveis_hoje,aulas_disponiveis_semana=aulas_disponiveis_semana,aulas_inscritas_hoje=aulas_inscritas_hoje,aulas_inscritas_semana=aulas_inscritas_semana)


@app.route('/alunoprofessoreslista')
def alunoprofessoreslista():
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'erro')
        return redirect(url_for('login'))

    if session.get('tipo') != 1:
        flash('Acesso negado. Somente alunos nessa pagina.', 'erro')
        return redirect(url_for('login'))

    cursor = con.cursor()

    cursor.execute("""
        SELECT 
            U.ID_USUARIO, 
            U.NOME, 
            U.EMAIL, 
            M.MODA
        FROM USUARIO U
        JOIN MODALIDADES M ON U.ID_MODALIDADE = M.ID_MODALIDADE
        WHERE U.TIPO = 2
          AND M.ATIVO = 1
        ORDER BY U.NOME
    """)

    profli = cursor.fetchall()
    cursor.close()

    return render_template('aluno-professores-lista.html',profli=profli,titulo='Dashboard aluno lista professor')

@app.route('/alunoavisos')
def alunoavisos():
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'erro')
        return redirect(url_for('login'))

    if session.get('tipo') != 1:
        flash('Acesso negado. Somente alunos nessa pagina.', 'erro')
        return redirect(url_for('login'))

    cursor = con.cursor()
    cursor.execute("select id_aviso, titulo, descricao from AVISO")
    avisoli = cursor.fetchall()
    cursor.close()

    return render_template('aluno-avisos.html', avisoli=avisoli, titulo='Dashboard aluno lista aviso')


@app.route('/alunoaulaslista', methods=['GET', 'POST'])
def alunoaulaslista():
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'erro')
        return redirect(url_for('login'))

    if session.get('tipo') != 1:
        flash('Acesso negado. Somente alunos nessa página.', 'erro')
        return redirect(url_for('login'))

    id_aluno = session['id_usuario']
    cursor = con.cursor()

    if request.method == 'POST':
        id_aula = request.form['id_aula']
        acao = request.form['acao']

        if acao == 'inscrever':

            # --- INÍCIO DA MODIFICAÇÃO 1: Verificação de Segurança (POST) ---
            # Verifica se a aula ainda está ativa ANTES de se inscrever
            cursor.execute("""
                           SELECT 1
                           FROM AULA A
                                    JOIN MODALIDADES M ON A.ID_MODALIDADE = M.ID_MODALIDADE
                           WHERE A.ID_AULA = ?
                             AND M.ATIVO = 1
                           """, (id_aula,))
            aula_ativa = cursor.fetchone()

            if not aula_ativa:
                flash('Não é possível se inscrever. Esta aula pertence a uma modalidade que foi desativada.', 'erro')
                cursor.close()
                return redirect(url_for('alunoaulaslista'))
            # --- FIM DA MODIFICAÇÃO 1 ---

            # (Sua lógica de verificação de vagas - está correta)
            cursor.execute("""
                           SELECT A.CAPACIDADE, COUNT(AA.ID_ALUNO) AS VAGAS_OCUPADAS
                           FROM AULA A
                                    LEFT JOIN AULA_ALUNO AA ON A.ID_AULA = AA.ID_AULA
                           WHERE A.ID_AULA = ?
                           GROUP BY A.ID_AULA, A.CAPACIDADE
                           """, (id_aula,))
            resultado_vagas = cursor.fetchone()
            capacidade_total = resultado_vagas[0] if resultado_vagas else 0
            vagas_ocupadas = resultado_vagas[1] if resultado_vagas else 0

            cursor.execute("SELECT 1 FROM AULA_ALUNO WHERE ID_ALUNO = ? AND ID_AULA = ?", (id_aluno, id_aula))
            ja_inscrito = cursor.fetchone()

            if vagas_ocupadas >= capacidade_total:
                flash('Esta aula está esgotada!', 'erro')
            elif ja_inscrito:
                flash('Você já está inscrito nesta aula.', 'erro')
            else:
                cursor.execute("INSERT INTO AULA_ALUNO (ID_ALUNO, ID_AULA) VALUES (?, ?)", (id_aluno, id_aula))
                con.commit()
                # --- INÍCIO DA MODIFICAÇÃO 2: Adicionar Flash de Sucesso ---
                flash('Inscrição realizada com sucesso!', 'success')
                # --- FIM DA MODIFICAÇÃO 2 ---

        elif acao == 'desinscrever':
            cursor.execute("DELETE FROM AULA_ALUNO WHERE ID_ALUNO = ? AND ID_AULA = ?", (id_aluno, id_aula))
            con.commit()
            # --- INÍCIO DA MODIFICAÇÃO 3: Adicionar Flash de Sucesso ---
            flash('Inscrição cancelada.', 'success')
            # --- FIM DA MODIFICAÇÃO 3 ---

        cursor.close()
        return redirect(url_for('alunoaulaslista'))

    # --- INÍCIO DA MODIFICAÇÃO 4: Corrigir Consulta SQL (GET) ---
    # 1. Adicionado JOIN MODALIDADES
    # 2. Adicionado WHERE M.ATIVO = 1
    # 3. Corrigido A.MODALIDADE para M.MODA
    cursor.execute("""
                   SELECT A.ID_AULA,
                          A.NOME,
                          A.DESCRICAO,
                          A.DIA_SEMANA,
                          A.HORARIO,
                          A.HORARIO_FINAL,
                          A.CAPACIDADE,
                          U.NOME             AS PROFESSOR,
                          M.MODA, -- Corrigido
                          COUNT(AA.ID_ALUNO) AS VAGAS_OCUPADAS
                   FROM AULA A
                            JOIN USUARIO U ON A.PROFESSOR_ID = U.ID_USUARIO
                            JOIN MODALIDADES M ON A.ID_MODALIDADE = M.ID_MODALIDADE -- Adicionado
                            LEFT JOIN AULA_ALUNO AA ON A.ID_AULA = AA.ID_AULA
                   WHERE M.ATIVO = 1 -- Adicionado
                   GROUP BY A.ID_AULA, A.NOME, A.DESCRICAO, A.DIA_SEMANA,
                            A.HORARIO, A.HORARIO_FINAL, A.CAPACIDADE, U.NOME,
                            M.MODA -- Corrigido
                   ORDER BY A.DIA_SEMANA, A.HORARIO
                   """)
    # --- FIM DA MODIFICAÇÃO 4 ---

    aulas_db = cursor.fetchall()

    # (Sua lógica de buscar inscrições - Correta)
    cursor.execute("SELECT ID_AULA FROM AULA_ALUNO WHERE ID_ALUNO = ?", (id_aluno,))
    inscricoes = {row[0] for row in cursor.fetchall()}

    # (Sua lógica de separar por dia - Correta)
    aulas_segunda = []
    aulas_terca = []
    aulas_quarta = []
    aulas_quinta = []
    aulas_sexta = []

    for aula in aulas_db:
        dia = aula[3]  # DIA_SEMANA (Índice correto)
        if dia == 1:
            aulas_segunda.append(aula)
        elif dia == 2:
            aulas_terca.append(aula)
        elif dia == 3:
            aulas_quarta.append(aula)
        elif dia == 4:
            aulas_quinta.append(aula)
        elif dia == 5:
            aulas_sexta.append(aula)

    cursor.close()

    # (Seu render_template - Correto)
    return render_template('aluno-aulas-lista.html',
                           titulo='Dashboard aluno',
                           inscricoes=inscricoes,
                           aulas_segunda=aulas_segunda,
                           aulas_terca=aulas_terca,
                           aulas_quarta=aulas_quarta,
                           aulas_quinta=aulas_quinta,
                           aulas_sexta=aulas_sexta)



@app.route('/alunoeditarconta', methods=['GET', 'POST'])
def alunoeditarconta():
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'erro')
        return redirect(url_for('login'))

    if session.get('tipo') != 1:
        flash('Acesso negado. Somente alunos nessa pagina.', 'erro')
        return redirect(url_for('login'))

    idaluno = session['id_usuario']
    cursor = con.cursor()

    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        telefone = request.form['telefone']
        senha = request.form['senha']
        confsenha = request.form['confsenha']

        if senha and senha != confsenha:
            flash('As senhas não conferem!', 'erro')
            return redirect(url_for('alunoeditarconta'))

        cursor.execute('SELECT 1 FROM usuario WHERE email = ? AND id_usuario != ?', (email, idaluno))
        if cursor.fetchone():
            flash("Esse email já está cadastrado por outro usuário.", 'erro')
            return redirect(url_for('alunoeditarconta'))

        if senha:
            maiusculo = minuscula = numero = caracterEspecial = False
            for s in senha:
                if s.isupper():
                    maiusculo = True
                elif s.islower():
                    minuscula = True
                elif s.isdigit():
                    numero = True
                elif not s.isalnum():
                    caracterEspecial = True

            if not (maiusculo and minuscula and numero and caracterEspecial):
                flash("Sua senha deve ter uma letra maiúscula, uma letra minúscula, um caractere especial e um número.",
                      'erro')
                return render_template("admin-editar-conta.html", nome=nome, email=email, telefone=telefone)

            senha_hash = generate_password_hash(senha)

            cursor.execute('UPDATE usuario SET nome = ?, email = ?, telefone = ?, senha = ? WHERE id_usuario = ?',
                           (nome, email, telefone, senha_hash, idaluno))
        else:
            cursor.execute('UPDATE usuario SET nome = ?, email = ?, telefone = ? WHERE id_usuario = ?',
                           (nome, email, telefone, idaluno))

        con.commit()
        cursor.close()

        flash('Conta atualizada com sucesso!', 'success')
        return redirect(url_for('alunodashbord'))

    cursor.execute("SELECT nome, email, telefone, senha FROM usuario WHERE id_usuario = ?", (idaluno,))
    dados = cursor.fetchone()
    cursor.close()

    if not dados:
        flash('Erro ao carregar informações da conta.', 'error')
        return redirect(url_for('alunodashbord'))

    nome, email, telefone, senha = dados
    return render_template('aluno-editar-conta.html', nome=nome, email=email, telefone=telefone)


@app.route('/dashbordadmin')
def dashbordadmin():
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'erro')
        return redirect(url_for('login'))

    if session.get('tipo') != 3:
        flash('Acesso negado. Somente administradores nessa pagina.', 'erro')
        return redirect(url_for('login'))

    cursor = con.cursor()

    cursor.execute("SELECT COUNT(*) FROM usuario WHERE tipo = 1")
    total_alunos = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM usuario WHERE tipo = 2")
    total_professores = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM usuario WHERE tipo = 3")
    total_admins = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM AULA")
    total_aula = cursor.fetchone()[0]

    cursor.close()

    return render_template('dashbord-admin.html', titulo='Dashboard Admin', total_alunos=total_alunos, total_professores=total_professores,total_admins=total_admins, total_aula=total_aula)


@app.route('/adminalunoslista')
def adminalunoslista():
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'erro')
        return redirect(url_for('login'))

    if session.get('tipo') != 3:
        flash('Acesso negado. Somente administradores nessa pagina.', 'erro')
        return redirect(url_for('login'))

    cursor = con.cursor()
    cursor.execute("select id_usuario, nome, email, tentativas from USUARIO WHERE tipo = 1")
    alunosli = cursor.fetchall()
    cursor.close()
    return render_template('admin-alunos-lista.html', alunosli=alunosli, titulo='Dashboard admin lista aluno')


@app.route('/adminresetartentativas', methods=['POST'])
def adminresetartentativas():
    # Verifica se o usuário está logado e é admin
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'erro')
        return redirect(url_for('login'))

    if session.get('tipo') != 3:
        flash('Acesso negado. Somente administradores nessa pagina.', 'erro')
        return redirect(url_for('login'))

    # Pega o id do usuário enviado pelo formulário
    id_usuario = request.form.get('id_usuario')

    cursor = con.cursor()
    # Atualiza tentativas para 0
    cursor.execute('UPDATE usuario SET tentativas = 0 WHERE id_usuario = ?', (id_usuario,))
    con.commit()
    cursor.close()

    flash('Tentativas resetadas com sucesso!', 'success')
    # Retorna para a página anterior
    return redirect(request.referrer)


@app.route('/admineditaralunos/<int:id>', methods=['GET', 'POST'])
def admineditaralunos(id):
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'erro')
        return redirect(url_for('login'))

    if session.get('tipo') != 3:
        flash('Acesso negado. Somente administradores nessa pagina.', 'erro')
        return redirect(url_for('login'))

    cursor = con.cursor()
    cursor.execute("SELECT nome, email, telefone, senha FROM usuario WHERE id_usuario = ?", (id,))
    usuario = cursor.fetchone()

    if not usuario:
        cursor.close()
        flash("Usuário não foi encontrado.", 'erro')
        return redirect(url_for('adminalunoslista'))

    nome, email, telefone, senha_atual = usuario

    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        telefone = request.form['telefone']
        senha = request.form['senha']
        confsenha = request.form['confsenha']

        if senha and senha != confsenha:
            flash('As senhas não conferem!', 'erro')
            return render_template("admin-editar-aluno.html", id=id, nome=nome, email=email, telefone=telefone)

        cursor.execute('SELECT 1 FROM usuario WHERE email = ? AND id_usuario != ?', (email, id))
        if cursor.fetchone():
            flash("Esse email já está cadastrado por outro usuário.", 'erro')
            return render_template("admin-editar-aluno.html", id=id, nome=nome, email=email, telefone=telefone)

        if senha:
            maiusculo = minuscula = numero = caracterEspecial = False
            for s in senha:
                if s.isupper():
                    maiusculo = True
                elif s.islower():
                    minuscula = True
                elif s.isdigit():
                    numero = True
                elif not s.isalnum():
                    caracterEspecial = True

            if not (maiusculo and minuscula and numero and caracterEspecial):
                flash("A senha deve conter letra maiúscula, minúscula, número e caractere especial.", 'erro')
                return render_template("admin-editar-aluno.html", id=id, nome=nome, email=email, telefone=telefone)

            senha_hash = generate_password_hash(senha)
            cursor.execute('UPDATE usuario SET nome = ?, email = ?, telefone = ?, senha = ? WHERE id_usuario = ?',
                            (nome, email, telefone, senha_hash, id))
        else:
            cursor.execute('UPDATE usuario SET nome = ?, email = ?, telefone = ? WHERE id_usuario = ?',
                            (nome, email, telefone, id))

        con.commit()
        cursor.close()
        flash('Usuário atualizado com sucesso!', 'success')
        return redirect(url_for('adminalunoslista'))

    cursor.close()
    return render_template('admin-editar-aluno.html', id=id, nome=nome, email=email, telefone=telefone)


@app.route('/adminexcluiralunos/<int:id>', methods=['GET', 'POST'])
def adminexcluiralunos(id):
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'erro')
        return redirect(url_for('login'))

    if session.get('tipo') != 3:
        flash('Acesso negado. Somente administradores nessa pagina.', 'erro')
        return redirect(url_for('login'))

    cursor = con.cursor()
    cursor.execute("SELECT nome, email FROM usuario WHERE id_usuario = ?", (id,))
    usuario = cursor.fetchone()

    if not usuario:
        cursor.close()
        flash("Usuário não encontrado.", 'erro')
        return redirect(url_for('adminalunoslista'))

    nome, email = usuario

    if request.method == 'POST':
        confirmar = request.form.get('confirmar')
        if confirmar == 'sim':
            cursor.execute("DELETE FROM usuario WHERE id_usuario = ?", (id,))
            con.commit()
            cursor.close()
            flash(f"O aluno '{nome}' foi excluído com sucesso.", 'success')
            return redirect(url_for('adminalunoslista'))

    cursor.close()
    return render_template('admin-excluir-aluno.html', id=id, nome=nome, email=email)

@app.route('/adminprofessoreslista')
def adminprofessoreslista():
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'erro')
        return redirect(url_for('login'))

    if session.get('tipo') != 3:
        flash('Acesso negado. Somente administradores nessa pagina.', 'erro')
        return redirect(url_for('login'))

    cursor = con.cursor()
    cursor.execute("""
                   SELECT U.ID_USUARIO,
                          U.NOME,
                          U.EMAIL,
                          M.MODA, -- Esta é a nova "especialidade" (o nome vindo da tabela MODALIDADES)
                          U.TENTATIVAS
                   FROM USUARIO AS U
                            LEFT JOIN MODALIDADES AS M ON U.ID_MODALIDADE = M.ID_MODALIDADE
                   WHERE U.TIPO = 2
                   ORDER BY U.NOME
                   """)
    profli = cursor.fetchall()
    cursor.close()
    return render_template('admin-professores-lista.html', profli=profli, titulo='Dashboard admin lista professores')


@app.route('/admineditarprofessor/<int:id>', methods=['GET', 'POST'])
def admineditarprofessor(id):
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'erro')
        return redirect(url_for('login'))

    if session.get('tipo') != 3:  # tipo 3 = admin
        flash('Acesso negado. Somente administradores nessa pagina.', 'erro')
        return redirect(url_for('login'))

    cursor = con.cursor()

    cursor.execute("SELECT 1 FROM AULA WHERE PROFESSOR_ID = ?", (id,))
    aula_existente = cursor.fetchone()

    if aula_existente:
        cursor.close()
        flash(f"Não é possível editar este professor, pois ele(a) já possui aulas cadastradas. ",'erro')

        return redirect(url_for('adminprofessoreslista'))

    cursor.execute("SELECT id_modalidade, moda FROM modalidades WHERE ATIVO = 1 ORDER BY moda")
    modalidades_lista = cursor.fetchall()

    if request.method == 'POST':

        nome = request.form['nome']
        email = request.form['email']
        telefone = request.form['telefone']
        especialidade_id = request.form['especialidade']
        senha = request.form['senha']
        confsenha = request.form['confsenha']

        if senha and senha != confsenha:
            flash('As senhas não conferem!', 'erro')
            return render_template("admin-editar-professor.html",
                                   id=id, modalidades=modalidades_lista,
                                   nome=nome, email=email, telefone=telefone,
                                   especialidade=especialidade_id)

        cursor.execute('SELECT 1 FROM usuario WHERE email = ? AND id_usuario != ?', (email, id))
        if cursor.fetchone():
            flash("Esse email já está cadastrado por outro usuário.", 'erro')
            return render_template("admin-editar-professor.html",
                                   id=id, modalidades=modalidades_lista,
                                   nome=nome, email=email, telefone=telefone,
                                   especialidade=especialidade_id)

        if senha:
            maiusculo = minuscula = numero = caracterEspecial = False
            for s in senha:
                if s.isupper():
                    maiusculo = True
                elif s.islower():
                    minuscula = True
                elif s.isdigit():
                    numero = True
                elif not s.isalnum():
                    caracterEspecial = True

            if not (maiusculo and minuscula and numero and caracterEspecial):
                flash("A senha deve conter letra maiúscula, minúscula, número e caractere especial.", 'erro')
                return render_template("admin-editar-professor.html",
                                       id=id, modalidades=modalidades_lista,
                                       nome=nome, email=email, telefone=telefone,
                                       especialidade=especialidade_id)

            senha_hash = generate_password_hash(senha)
            cursor.execute("""
                           UPDATE usuario
                           SET nome = ?, email = ?, telefone = ?, ID_MODALIDADE = ?, senha = ?
                           WHERE id_usuario = ?
                           """, (nome, email, telefone, especialidade_id, senha_hash, id))

        else:
            cursor.execute("""
                UPDATE usuario 
                SET nome = ?, email = ?, telefone = ?, ID_MODALIDADE = ? 
                WHERE id_usuario = ?
            """, (nome, email, telefone, especialidade_id, id))

        con.commit()
        cursor.close()
        flash('Professor atualizado com sucesso!', 'success')
        return redirect(url_for('adminprofessoreslista'))

    else:
        cursor.execute("SELECT nome, email, telefone, ID_MODALIDADE FROM usuario WHERE id_usuario = ?", (id,))
        professor = cursor.fetchone()

        if not professor:
            cursor.close()
            flash("Professor não foi encontrado.", 'erro')
            return redirect(url_for('adminprofessoreslista'))

        nome_atual, email_atual, telefone_atual, especialidade_atual_id = professor
        cursor.close()

        return render_template(
            'admin-editar-professor.html',id=id,modalidades=modalidades_lista,nome=nome_atual,email=email_atual,telefone=telefone_atual,especialidade=especialidade_atual_id)

@app.route('/adminexcluirprofessor/<int:id>', methods=['GET', 'POST'])
def adminexcluirprofessor(id):
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'erro')
        return redirect(url_for('login'))

    if session.get('tipo') != 3:
        flash('Acesso negado. Somente administradores nessa pagina.', 'erro')
        return redirect(url_for('login'))

    cursor = con.cursor()
    cursor.execute("SELECT nome, email FROM usuario WHERE id_usuario = ?", (id,))
    usuario = cursor.fetchone()

    if not usuario:
        cursor.close()
        flash("Usuário não encontrado.", 'erro')
        return redirect(url_for('adminprofessoreslista'))

    nome, email = usuario

    if request.method == 'POST':
        confirmar = request.form.get('confirmar')
        if confirmar == 'sim':

            cursor.execute("SELECT 1 FROM AULA WHERE PROFESSOR_ID = ?", (id,))
            aula_existente = cursor.fetchone()

            if aula_existente:
                cursor.close()
                flash(
                    f"Não é possível excluir o professor '{nome}', pois ele(a) já possui aulas cadastradas no sistema.",
                    'erro')
                return redirect(url_for('adminprofessoreslista'))

            cursor.execute("DELETE FROM usuario WHERE id_usuario = ?", (id,))
            con.commit()
            cursor.close()
            flash(f"O professor '{nome}' foi excluído com sucesso.", 'success')
            return redirect(url_for('adminprofessoreslista'))

        else:
            cursor.close()
            flash("Exclusão cancelada.", 'info')
            return redirect(url_for('adminprofessoreslista'))

    cursor.close()
    return render_template('admin-excluir-professor.html', id=id, nome=nome, email=email)

@app.route('/adminadmlista')
def adminadmlista():
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'erro')
        return redirect(url_for('login'))

    if session.get('tipo') != 3:
        flash('Acesso negado. Somente administradores nessa pagina.', 'erro')
        return redirect(url_for('login'))

    id_admin_logado = session['id_usuario']

    cursor = con.cursor()
    cursor.execute("SELECT id_usuario, nome, email, tentativas FROM usuario WHERE tipo = 3 AND id_usuario != ?", (id_admin_logado,))
    admli = cursor.fetchall()
    cursor.close()

    return render_template('admin-adm-lista.html', admli=admli, titulo='Dashboard - Lista de Admins')


@app.route('/admineditaradm/<int:id>', methods=['GET', 'POST'])
def admineditaradm(id):
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'erro')
        return redirect(url_for('login'))

    if session.get('tipo') != 3:
        flash('Acesso negado. Somente administradores nessa pagina.', 'erro')
        return redirect(url_for('login'))

    cursor = con.cursor()
    cursor.execute("SELECT nome, email, telefone, senha FROM usuario WHERE id_usuario = ?", (id,))
    usuario = cursor.fetchone()

    if not usuario:
        cursor.close()
        flash("Usuário não foi encontrado.", 'erro')
        return redirect(url_for('adminadmlista'))

    nome, email, telefone, senha_atual = usuario

    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        telefone = request.form['telefone']
        senha = request.form['senha']
        confsenha = request.form['confsenha']

        if senha and senha != confsenha:
            flash('As senhas não conferem!', 'erro')
            return render_template("admin-editar-adm-.html", id=id, nome=nome, email=email, telefone=telefone)

        cursor.execute('SELECT 1 FROM usuario WHERE email = ? AND id_usuario != ?', (email, id))
        if cursor.fetchone():
            flash("Esse email já está cadastrado por outro usuário.", 'erro')
            return render_template("admin-editar-aluno.html", id=id, nome=nome, email=email, telefone=telefone)

        if senha:
            maiusculo = minuscula = numero = caracterEspecial = False
            for s in senha:
                if s.isupper():
                    maiusculo = True
                elif s.islower():
                    minuscula = True
                elif s.isdigit():
                    numero = True
                elif not s.isalnum():
                    caracterEspecial = True

            if not (maiusculo and minuscula and numero and caracterEspecial):
                flash("A senha deve conter letra maiúscula, minúscula, número e caractere especial.", 'erro')
                return render_template("admin-editar-adm-.html", id=id, nome=nome, email=email, telefone=telefone)

            senha_hash = generate_password_hash(senha)
            cursor.execute('UPDATE usuario SET nome = ?, email = ?, telefone = ?, senha = ? WHERE id_usuario = ?',
                            (nome, email, telefone, senha_hash, id))
        else:
            cursor.execute('UPDATE usuario SET nome = ?, email = ?, telefone = ? WHERE id_usuario = ?',
                            (nome, email, telefone, id))

        con.commit()
        cursor.close()
        flash('Usuário atualizado com sucesso!', 'success')
        return redirect(url_for('adminadmlista'))

    cursor.close()
    return render_template('admin-editar-adm-.html', id=id, nome=nome, email=email, telefone=telefone)


@app.route('/adminexluiradmin/<int:id>', methods=['GET', 'POST'])
def adminexluiradmin(id):
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'erro')
        return redirect(url_for('login'))

    if session.get('tipo') != 3:
        flash('Acesso negado. Somente administradores nessa pagina.', 'erro')
        return redirect(url_for('login'))

    cursor = con.cursor()
    cursor.execute("SELECT nome, email FROM usuario WHERE id_usuario = ?", (id,))
    usuario = cursor.fetchone()

    if not usuario:
        cursor.close()
        flash("Usuário não encontrado.", 'erro')
        return redirect(url_for('adminadmlista'))

    nome, email = usuario

    if request.method == 'POST':
        confirmar = request.form.get('confirmar')
        if confirmar == 'sim':
            cursor.execute("DELETE FROM usuario WHERE id_usuario = ?", (id,))
            con.commit()
            cursor.close()
            flash(f"O Admin '{nome}' foi excluído com sucesso.", 'success')
            return redirect(url_for('adminadmlista'))
        else:
            cursor.close()
            flash("Exclusão cancelada.", 'info')
            return redirect(url_for('adminadmlista'))

    cursor.close()
    return render_template('admin-excluir-admin.html', id=id, nome=nome, email=email)


@app.route('/adminadicionarusuario', methods=['GET', 'POST'])
def adminadicionarusuario():
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'erro')
        return redirect(url_for('login'))

    if session.get('tipo') != 3:
        flash('Acesso negado. Somente administradores nessa pagina.', 'erro')
        return redirect(url_for('login'))

    cursor = con.cursor()
    cursor.execute("SELECT ID_MODALIDADE, MODA FROM MODALIDADES WHERE ATIVO = 1 ORDER BY MODA")
    modalidades = cursor.fetchall()


    if request.method == 'POST':
        tipo = int(request.form['tipos'])
        nome = request.form['nome']
        email = request.form['email']
        telefone = request.form['telefone']
        especialidade_id = request.form.get('especialidade')
        senha = request.form['senha']
        confsenha = request.form['confsenha']

        cursor = con.cursor()
        try:
            cursor.execute("SELECT id_usuario FROM usuario WHERE email = ?", (email,))
            if cursor.fetchone():
                flash("Este email já está cadastrado!", 'erro')
                return render_template('admin-adicionar-usuario.html', nome=nome, email=email, telefone=telefone,
                                       especialidade=especialidade_id, tipos=tipo, modalidades=modalidades)

            if senha != confsenha:
                flash('As senhas não conferem!', 'erro')
                return render_template('admin-adicionar-usuario.html', nome=nome, email=email, telefone=telefone,
                                       especialidade=especialidade_id, tipos=tipo, modalidades=modalidades)

            senha_hash = generate_password_hash(senha)

            if tipo == 2:

                if not especialidade_id:
                    flash('Você deve selecionar uma especialidade para o professor.', 'erro')
                    return render_template('admin-adicionar-usuario.html', nome=nome, email=email, telefone=telefone,
                                           especialidade=especialidade_id, tipos=tipo, modalidades=modalidades)

                cursor.execute("""
                               INSERT INTO usuario (nome, email, telefone, ID_MODALIDADE, senha, tipo, tentativas)
                               VALUES (?, ?, ?, ?, ?, ?, 0)
                               """, (nome, email, telefone, especialidade_id, senha_hash, tipo))
            else:

                cursor.execute("""
                    INSERT INTO usuario (nome, email, telefone, ID_MODALIDADE, senha, tipo, tentativas)
                    VALUES (?, ?, ?, ?, ?, ?, 0)
                    """, (nome, email, telefone, None, senha_hash, tipo))

            con.commit()
            flash('Usuário cadastrado com sucesso!', 'success')
            return redirect(url_for('dashbordadmin'))

        finally:
            cursor.close()

    cursor.close()
    return render_template('admin-adicionar-usuario.html', modalidades=modalidades)

@app.route('/adminmodalidadeslista', methods=['GET', 'POST'])
def adminmodalidadeslista():
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'erro')
        return redirect(url_for('login'))

    if session.get('tipo') != 3:
        flash('Acesso negado. Somente administradores nessa pagina.', 'erro')
        return redirect(url_for('login'))

    cursor = con.cursor()

    if request.method == 'POST':
        id_modalidade = request.form['id_modalidade']
        acao = request.form['acao']

        if acao == 'desativar':
            cursor.execute("SELECT 1 FROM AULA WHERE ID_MODALIDADE = ?", (id_modalidade,))
            aula_existente = cursor.fetchone()

            if aula_existente:
                flash(
                    'Não é possível desativar esta modalidade, pois ela já está sendo usada por aulas cadastradas. Exclua as aulas primeiro.',
                    'erro')
            else:
                cursor.execute("UPDATE MODALIDADES SET ATIVO = 0 WHERE ID_MODALIDADE = ?", (id_modalidade,))
                con.commit()
                flash('Modalidade desativada com sucesso.', 'success')

        elif acao == 'ativar':
            cursor.execute("UPDATE MODALIDADES SET ATIVO = 1 WHERE ID_MODALIDADE = ?", (id_modalidade,))
            con.commit()
            flash('Modalidade ativada com sucesso.', 'success')

        cursor.close()
        return redirect(url_for('adminmodalidadeslista'))

    cursor.execute("SELECT ID_MODALIDADE, MODA, VAGAS, ATIVO FROM MODALIDADES")
    modali = cursor.fetchall()
    cursor.close()

    return render_template('admin-modalidades-lista.html', modali=modali, titulo='Dashboard admin lista aulas')


@app.route('/adminadicionarmodalidades', methods=['POST', 'GET'])
def adminadicionarmodalidades():
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'erro')
        return redirect(url_for('login'))

    if session.get('tipo') != 3:
        flash('Acesso negado. Somente administradores nessa pagina', 'erro')
        return redirect(url_for('login'))

    if request.method == 'POST':
        moda = request.form['moda']
        vagas = request.form['vagas']

        if not moda or not vagas:
            flash('Nome da modalidade e vagas são obrigatórios.', 'erro')
            return render_template('admin-adicionar-modalidades.html', titulo='Adicionar modalidade')

        if int(vagas) <= 0:
            flash('O número de vagas deve ser maior que zero.', 'erro')
            return render_template('admin-adicionar-modalidades.html', titulo='Adicionar modalidade', moda=moda,vagas=vagas)

        cursor = con.cursor()

        cursor.execute("SELECT 1 FROM MODALIDADES WHERE UPPER(MODA) = UPPER(?)", (moda,))

        conflito_moda = cursor.fetchone()

        if conflito_moda:
            flash('Já existe essa modalidade.', 'erro')
            cursor.close()

            return render_template('admin-adicionar-modalidades.html', titulo='Adicionar modalidade', moda=moda,vagas=vagas)

        moda_padronizada = moda.title()

        cursor.execute("INSERT INTO modalidades (moda, vagas) VALUES (?, ?)", (moda_padronizada, vagas))

        con.commit()
        cursor.close()
        flash('Modalidade adicionada com sucesso!', 'success')
        return redirect(url_for('adminmodalidadeslista'))

    return render_template('admin-adicionar-modalidades.html', titulo='Adicionar modalidade')

@app.route('/adminexcluirmodalidades/<int:id>', methods=['GET', 'POST'])
def adminexcluirmodalidades(id):
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'erro')
        return redirect(url_for('login'))

    if session.get('tipo') != 3:
        flash('Acesso negado. Somente administradores nessa pagina', 'erro')
        return redirect(url_for('login'))

    cursor = con.cursor()

    if request.method == 'GET':
        cursor.execute("SELECT id_modalidade, moda, vagas FROM modalidades WHERE id_modalidade = ?", (id,))
        modalidade = cursor.fetchone()
        cursor.close()

        if not modalidade:
            flash("Modalidade não encontrada.", "erro")
            return redirect(url_for('adminmodalidadeslista'))

        return render_template('admin-excluir-modalidades.html', modalidade=modalidade)

    cursor.execute("SELECT moda FROM modalidades WHERE id_modalidade = ?", (id,))
    modalidade_record = cursor.fetchone()

    if not modalidade_record:
        flash("Modalidade não encontrada.", "erro")
        cursor.close()
        return redirect(url_for('adminmodalidadeslista'))

    nome_da_modalidade = modalidade_record[0]

    cursor.execute("SELECT 1 FROM AULA WHERE ID_MODALIDADE = ?", (id,))
    aula_existente = cursor.fetchone()

    if aula_existente:
        flash(f"Não é possível excluir a modalidade '{nome_da_modalidade}', pois já existem AULAS cadastradas nela.",
              "erro")
        cursor.close()
        return redirect(url_for('adminmodalidadeslista'))

    cursor.execute("SELECT 1 FROM USUARIO WHERE ID_MODALIDADE = ? AND TIPO = 2", (id,))
    professor_existente = cursor.fetchone()

    if professor_existente:
        flash(
            f"Não é possível excluir a modalidade '{nome_da_modalidade}', pois existem PROFESSORES cadastrados com essa especialidade.",
            "erro")
        cursor.close()
        return redirect(url_for('adminmodalidadeslista'))

    cursor.execute("DELETE FROM modalidades WHERE id_modalidade = ?", (id,))
    con.commit()
    cursor.close()

    flash("Modalidade excluída com sucesso!", "success")
    return redirect(url_for('adminmodalidadeslista'))


@app.route('/admineditarmodalidades/<int:id>', methods=['GET', 'POST'])
def admineditarmodalidades(id):
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'erro')
        return redirect(url_for('login'))

    if session.get('tipo') != 3:
        flash('Acesso negado. Somente administradores nessa pagina', 'erro')
        return redirect(url_for('login'))

    cursor = con.cursor()

    if request.method == 'POST':

        moda_nova = request.form['moda']
        vagas_novo = request.form['vagas']

        cursor.execute("SELECT 1 FROM MODALIDADES WHERE UPPER(MODA) = UPPER(?) AND ID_MODALIDADE != ?", (moda_nova, id))
        conflito_moda = cursor.fetchone()

        if conflito_moda:
            flash('Já existe outra modalidade com esse nome.', 'erro')
            cursor.close()

            return render_template('admin-editar-modalidades.html',moda_atual=moda_nova,  vagas_atual=vagas_novo, id=id,titulo='Editar Modalidade')

        moda_padronizada = moda_nova.title()

        cursor.execute("UPDATE modalidades SET moda = ?, vagas = ? WHERE ID_MODALIDADE = ?",
                       (moda_padronizada, vagas_novo, id))

        con.commit()
        cursor.close()

        flash('Modalidade atualizada com sucesso!', 'success')
        return redirect(url_for('adminmodalidadeslista'))

    cursor.execute("SELECT moda, vagas FROM modalidades WHERE id_modalidade = ?", (id,))
    modalidade = cursor.fetchone()

    if not modalidade:
        cursor.close()
        flash('Modalidade não encontrada.', 'erro')
        return redirect(url_for('adminmodalidadeslista'))

    moda_atual, vagas_atual = modalidade
    cursor.close()

    return render_template('admin-editar-modalidades.html',moda_atual=moda_atual,vagas_atual=vagas_atual,id=id,titulo='Editar Modalidade')

@app.route('/adminaulaslista')
def adminaulaslista():
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'erro')
        return redirect(url_for('login'))

    if session.get('tipo') != 3:
        flash('Acesso negado. Somente administradores nessa pagina.', 'erro')
        return redirect(url_for('login'))

    cursor = con.cursor()

    cursor.execute("""SELECT 
                   A.ID_AULA,
                   A.NOME,
                   A.DESCRICAO,
                   A.DIA_SEMANA,
                   A.HORARIO,
                   A.HORARIO_FINAL,
                   A.CAPACIDADE,   
                   U.NOME AS PROFESSOR,
                   M.MODA,
                   COUNT(AA.ID_ALUNO) AS VAGAS_OCUPADAS 
               FROM AULA A
               JOIN USUARIO U ON A.PROFESSOR_ID = U.ID_USUARIO
               JOIN MODALIDADES M ON A.ID_MODALIDADE = M.ID_MODALIDADE 
               LEFT JOIN AULA_ALUNO AA ON A.ID_AULA = AA.ID_AULA
               GROUP BY 
                   A.ID_AULA, A.NOME, A.DESCRICAO, A.DIA_SEMANA,
                   A.HORARIO, A.HORARIO_FINAL, A.CAPACIDADE, U.NOME,
                   M.MODA
               ORDER BY A.DIA_SEMANA, A.HORARIO
           """)
    aulas_db = cursor.fetchall()
    cursor.close()

    aulas_segunda = []
    aulas_terca = []
    aulas_quarta = []
    aulas_quinta = []
    aulas_sexta = []

    for aula in aulas_db:
        dia = aula[3]

        if dia == 1:
            aulas_segunda.append(aula)
        elif dia == 2:
            aulas_terca.append(aula)
        elif dia == 3:
            aulas_quarta.append(aula)
        elif dia == 4:
            aulas_quinta.append(aula)
        elif dia == 5:
            aulas_sexta.append(aula)

    return render_template('admin-aulas-listas.html',titulo='Dashboard admin lista aulas',aulas_segunda=aulas_segunda,aulas_terca=aulas_terca,aulas_quarta=aulas_quarta,aulas_quinta=aulas_quinta,aulas_sexta=aulas_sexta)


@app.route('/adminadicionaraula', methods=['GET', 'POST'])
def adminadicionaraula():
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'erro')
        return redirect(url_for('login'))

    if session.get('tipo') != 3:
        flash('Acesso negado. Somente administradores nessa página', 'erro')
        return redirect(url_for('login'))

    cursor = con.cursor()

    if request.method == 'POST':

        nome = request.form['nome']
        descricao = request.form.get('descricao')
        dia_semana = request.form['data_aula']
        horario = request.form['horario']
        horario_final = request.form['horario_final']
        capacidade = request.form.get('capacidade')
        id_da_modalidade = request.form['id_modalidade']
        professor_id = request.form['professor_id']

        horario_minimo = "07:00"
        horario_maximo = "22:00"

        if horario_final <= horario:
            flash('O horário de término deve ser maior que o horário de início!', 'erro')
            cursor.close()
            return redirect(url_for('adminadicionaraula'))

        if horario < horario_minimo or horario > horario_maximo:
            flash(f'O horário de início deve estar entre {horario_minimo} e {horario_maximo}!', 'erro')
            cursor.close()
            return redirect(url_for('adminadicionaraula'))

        if horario_final < horario_minimo or horario_final > horario_maximo:
            flash(f'O horário de término deve estar entre {horario_minimo} e {horario_maximo}!', 'erro')
            cursor.close()
            return redirect(url_for('adminadicionaraula'))

        cursor.execute("SELECT 1 FROM AULA WHERE UPPER(NOME) = UPPER(?)", (nome,))
        conflito_nome = cursor.fetchone()

        if conflito_nome:
            flash('Ja existe uma aula com esse nome', 'erro')
            cursor.close()
            return redirect(url_for('adminadicionaraula'))

        cursor.execute("""
                    SELECT 1 FROM AULA 
                    WHERE PROFESSOR_ID = ? 
                      AND DIA_SEMANA = ?   
                      AND (HORARIO < ?) 
                      AND (HORARIO_FINAL > ?)
                """, (professor_id, dia_semana, horario_final, horario))
        conflito = cursor.fetchone()

        if conflito:
            flash('O professor já possui uma aula nesse dia e horário!', 'erro')
            cursor.close()
            return redirect(url_for('adminadicionaraula'))

        nome_padronizado = nome.title()

        descricao_padronizada = descricao.capitalize()

        cursor.execute("""
            INSERT INTO AULA 
                (NOME, DESCRICAO, DIA_SEMANA, HORARIO, HORARIO_FINAL, CAPACIDADE, PROFESSOR_ID, ID_MODALIDADE) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (nome_padronizado, descricao_padronizada, dia_semana, horario, horario_final, capacidade, professor_id, id_da_modalidade))

        con.commit()
        cursor.close()
        flash('Aula adicionada com sucesso!', 'success')
        return redirect(url_for('adminaulaslista'))

    cursor.execute("""
        SELECT ID_MODALIDADE, MODA, VAGAS 
        FROM MODALIDADES 
        WHERE ATIVO = 1 
        ORDER BY MODA
    """)
    modalidades_lista = cursor.fetchall()

    cursor.execute("""
        SELECT 
            U.ID_USUARIO,
            U.NOME,
            U.ID_MODALIDADE 
        FROM USUARIO AS U
        JOIN MODALIDADES AS M ON U.ID_MODALIDADE = M.ID_MODALIDADE
        WHERE U.TIPO = 2
          AND M.ATIVO = 1
        ORDER BY U.NOME
    """)
    professores_lista = cursor.fetchall()

    cursor.close()

    return render_template('admin-adicionar-aula.html',modalidades=modalidades_lista,professores=professores_lista,titulo='Dashboard admin adicionar aula')

@app.route('/adminalunosmatriculados/<int:aula_id>')
def adminalunosmatriculados(aula_id):
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'erro')
        return redirect(url_for('login'))

    if session.get('tipo') != 3:
        flash('Acesso negado. Somente administradores nessa pagina', 'erro')
        return redirect(url_for('login'))

    cursor = con.cursor()

    cursor.execute("SELECT NOME FROM AULA WHERE ID_AULA = ?", (aula_id,))
    aula = cursor.fetchone()

    # Pega alunos matriculados na aula
    cursor.execute("SELECT U.ID_USUARIO, U.NOME, U.EMAIL FROM AULA_ALUNO AA JOIN USUARIO U ON AA.ID_ALUNO = U.ID_USUARIO WHERE AA.ID_AULA = ?",
                   (aula_id,))
    alunosmatriculado = cursor.fetchall()

    cursor.close()

    return render_template('admin-alunos-matriculados.html', aula=aula, alunosmatriculado=alunosmatriculado)


@app.route('/admineditaraula/<int:id>', methods=['GET', 'POST'])
def admineditaraula(id):
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'erro')
        return redirect(url_for('login'))

    if session.get('tipo') != 3:
        flash('Acesso negado. Somente administradores nessa página.', 'erro')
        return redirect(url_for('login'))

    cursor = con.cursor()

    cursor.execute("""
        SELECT ID_AULA, NOME, DESCRICAO, DIA_SEMANA, HORARIO, HORARIO_FINAL, PROFESSOR_ID, CAPACIDADE 
        FROM AULA WHERE ID_AULA = ?
    """, (id,))
    aula = cursor.fetchone()

    if not aula:
        flash('Aula não encontrada.', 'erro')
        cursor.close()
        return redirect(url_for('adminaulaslista'))

    professor_id_original = aula[6]

    if request.method == 'POST':
        nome = request.form['nome']
        descricao = request.form['descricao']
        dia_semana = request.form['data_aula']
        horario = request.form['horario']
        horario_final = request.form['horario_final']
        capacidade = request.form.get('capacidade')

        horario_minimo = "07:00"
        horario_maximo = "22:00"

        if horario_final <= horario:
            flash('O horário de término deve ser maior que o horário de início!', 'erro')
            cursor.close()
            return redirect(url_for('admineditaraula', id=id))

        if horario < horario_minimo or horario > horario_maximo:
            flash(f'O horário de início deve estar entre {horario_minimo} e {horario_maximo}!', 'erro')
            cursor.close()
            return redirect(url_for('admineditaraula', id=id))

        if horario_final < horario_minimo or horario_final > horario_maximo:
            flash(f'O horário de término deve estar entre {horario_minimo} e {horario_maximo}!', 'erro')
            cursor.close()
            return redirect(url_for('admineditaraula', id=id))

        cursor.execute("SELECT 1 FROM AULA WHERE NOME = ? AND ID_AULA != ?", (nome, id))
        conflito_nome = cursor.fetchone()

        if conflito_nome:
            flash('Ja existe uma aula com esse nome', 'erro')
            cursor.close()
            return redirect(url_for('admineditaraula', id=id))

        cursor.execute("""
            SELECT 1 FROM AULA 
            WHERE PROFESSOR_ID = ? 
              AND DIA_SEMANA = ? 
              AND (HORARIO < ?) 
              AND (HORARIO_FINAL > ?)
              AND ID_AULA != ? 
        """, (professor_id_original, dia_semana, horario_final, horario, id))
        conflito_horario = cursor.fetchone()

        if conflito_horario:
            flash('Este professor já possui outra aula que conflita com este novo dia/horário!', 'erro')
            cursor.close()
            return redirect(url_for('admineditaraula', id=id))

        cursor.execute("""
            UPDATE AULA 
            SET NOME = ?, DESCRICAO = ?, DIA_SEMANA = ?, HORARIO = ?, HORARIO_FINAL = ?, CAPACIDADE = ?
            WHERE ID_AULA = ?
        """, (nome, descricao, dia_semana, horario, horario_final, capacidade, id))

        con.commit()
        cursor.close()
        flash('Aula atualizada com sucesso!', 'success')
        return redirect(url_for('adminaulaslista'))

    cursor.close()
    return render_template('admin-editar-aula.html', aula=aula, titulo='Editar Aula')

@app.route('/adminexcluiraula/<int:aula_id>', methods=['GET', 'POST'])
def adminexcluiraula(aula_id):
    if 'id_usuario' not in session or session.get('tipo') != 3:
        flash('Acesso negado.', 'erro')
        return redirect(url_for('login'))

    cursor = con.cursor()

    if request.method == 'POST':
        titulo = request.form['titulo']
        descricao = request.form['descricao']

        cursor.execute("INSERT INTO AVISO (TITULO, DESCRICAO) VALUES (?, ?)",
                       (titulo, descricao))

        cursor.execute("DELETE FROM AULA_ALUNO WHERE ID_AULA = ?", (aula_id,))

        cursor.execute("DELETE FROM AULA WHERE ID_AULA = ?", (aula_id,))

        con.commit()
        cursor.close()
        flash('Aviso adicionado e aula excluída com todos os alunos inscritos!', 'success')
        return redirect(url_for('adminaulaslista'))

    cursor.close()
    return render_template('admin-excluir-aula.html', aula_id=aula_id)

@app.route('/adminavisos')
def adminavisos():
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'erro')
        return redirect(url_for('login'))

    if session.get('tipo') != 3:
        flash('Acesso negado. Somente administradores nessa pagina', 'erro')
        return redirect(url_for('login'))

    cursor = con.cursor()
    cursor.execute("select id_aviso, titulo, descricao from AVISO")
    avisoli = cursor.fetchall()
    cursor.close()
    return render_template('admin-avisos.html', avisoli=avisoli, titulo='Dashboard admin lista aluno')


@app.route('/adminadicionaraviso', methods=['POST','GET'])
def adminadicionaraviso():
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'erro')
        return redirect(url_for('login'))

    if session.get('tipo') != 3:
        flash('Acesso negado. Somente administradores nessa pagina', 'erro')
        return redirect(url_for('login'))

    if request.method == 'POST':
        titulo = request.form['titulo']
        descricao = request.form['descricao']

        titulo_padronizado = titulo.title()
        descricao_padronizada = descricao.capitalize()

        cursor = con.cursor()
        cursor.execute("INSERT INTO aviso (titulo, descricao) VALUES (?, ?)", (titulo_padronizado, descricao_padronizada))
        con.commit()
        cursor.close()
        flash('Aviso adicionado com sucesso!', 'success')
        return redirect(url_for('adminavisos'))

    return render_template('admin-adicionar-aviso.html', titulo='Adicionar Aviso')


@app.route('/adminexcluiraviso/<int:id>', methods=['GET', 'POST'])
def adminexcluiraviso(id):
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'erro')
        return redirect(url_for('login'))

    if session.get('tipo') != 3:
        flash('Acesso negado. Somente administradores nessa pagina', 'erro')
        return redirect(url_for('login'))

    cursor = con.cursor()

    if request.method == 'GET':
        # Busca o aviso pelo ID e mostra a tela de confirmação
        cursor.execute("SELECT id_aviso, titulo, descricao FROM aviso WHERE id_aviso = ?", (id,))
        aviso = cursor.fetchone()
        cursor.close()

        if not aviso:
            flash("Aviso não encontrado.", "erro")
            return redirect(url_for('adminavisos'))

        return render_template('admin-excluir-aviso.html', aviso=aviso)

    # Se for POST, realmente exclui
    cursor.execute("DELETE FROM aviso WHERE id_aviso = ?", (id,))
    con.commit()
    cursor.close()

    flash("Aviso excluído com sucesso!", "success")
    return redirect(url_for('adminavisos'))


@app.route('/admineditaraviso/<int:id>', methods=['GET', 'POST'])
def admineditaraviso(id):
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'erro')
        return redirect(url_for('login'))

    if session.get('tipo') != 3:
        flash('Acesso negado. Somente administradores nessa pagina', 'erro')
        return redirect(url_for('login'))
    cursor = con.cursor()

    # Busca os dados atuais do aviso
    cursor.execute("SELECT titulo, descricao FROM aviso WHERE id_aviso = ?", (id,))
    aviso = cursor.fetchone()

    if not aviso:
        cursor.close()
        flash('Aviso não encontrado.', 'erro')
        return redirect(url_for('adminavisos'))

    titulo_atual, descricao_atual = aviso

    if request.method == 'POST':
        titulo = request.form['titulo']
        descricao = request.form['descricao']

        cursor.execute("UPDATE aviso SET titulo = ?, descricao = ? WHERE id_aviso = ?",
                       (titulo, descricao, id))
        con.commit()
        cursor.close()

        flash('Aviso atualizado com sucesso!', 'success')
        return redirect(url_for('adminavisos'))

    cursor.close()
    return render_template('admin-editar-aviso.html', titulo_aviso=titulo_atual, descricao_aviso=descricao_atual, id=id)


@app.route('/admineditarconta', methods=['GET', 'POST'])
def admineditarconta():
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'erro')
        return redirect(url_for('login'))

    if session.get('tipo') != 3:
        flash('Acesso negado. Somente administradores nessa pagina', 'erro')
        return redirect(url_for('login'))

    idadmin = session['id_usuario']
    cursor = con.cursor()

    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        telefone = request.form['telefone']
        senha = request.form['senha']
        confsenha = request.form['confsenha']

        if senha and senha != confsenha:
            flash('As senhas não conferem!', 'erro')
            return redirect(url_for('admineditarconta'))

        cursor.execute('SELECT 1 FROM usuario WHERE email = ? AND id_usuario != ?', (email, idadmin))
        if cursor.fetchone():
            flash("Esse email já está cadastrado por outro usuário.", 'erro')
            return redirect(url_for('admineditarconta'))

        if senha:
            maiusculo = minuscula = numero = caracterEspecial = False
            for s in senha:
                if s.isupper():
                    maiusculo = True
                elif s.islower():
                    minuscula = True
                elif s.isdigit():
                    numero = True
                elif not s.isalnum():
                    caracterEspecial = True

            if not (maiusculo and minuscula and numero and caracterEspecial):
                flash("Sua senha deve ter uma letra maiúscula, uma letra minúscula, um caractere especial e um número.",
                      'erro')
                return render_template("admin-editar-conta.html", nome=nome, email=email, telefone=telefone)

            senha_hash = generate_password_hash(senha)

            cursor.execute('UPDATE usuario SET nome = ?, email = ?, telefone = ?, senha = ? WHERE id_usuario = ?',
                           (nome, email, telefone, senha_hash, idadmin))
        else:
            cursor.execute('UPDATE usuario SET nome = ?, email = ?, telefone = ? WHERE id_usuario = ?',
                           (nome, email, telefone, idadmin))

        con.commit()
        cursor.close()

        flash('Conta atualizada com sucesso!', 'success')
        return redirect(url_for('dashbordadmin'))

    cursor.execute("SELECT nome, email, telefone, senha FROM usuario WHERE id_usuario = ?", (idadmin,))
    dados = cursor.fetchone()
    cursor.close()

    if not dados:
        flash('Erro ao carregar informações da conta.', 'error')
        return redirect(url_for('dashbordadmin'))

    nome, email, telefone, senha = dados

    return render_template('admin-editar-conta.html', nome=nome, email=email, telefone=telefone)


@app.route('/professordashbord')
def professordashbord():
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'erro')
        return redirect(url_for('login'))

    if session.get('tipo') != 2:
        flash('Acesso negado. Apenas professores nessa pagina.', 'erro')
        return redirect(url_for('login'))

    id_professor = session['id_usuario']


    hoje = date.today()

    dia_semana_hoje = hoje.weekday() + 1

    cursor = con.cursor()

    cursor.execute("""
                   SELECT COUNT(*)
                   FROM AULA
                   WHERE PROFESSOR_ID = ?
                     AND DIA_SEMANA = ?
                   """, (id_professor, dia_semana_hoje))
    total_hoje = cursor.fetchone()[0]

    cursor.execute("""
                   SELECT COUNT(*)
                   FROM AULA
                   WHERE PROFESSOR_ID = ?
                   """, (id_professor,))
    total_semana = cursor.fetchone()[0]


    cursor.close()

    return render_template('professor-dashbord.html',titulo='Dashboard Professor',total_hoje=total_hoje,total_semana=total_semana)
@app.route('/professoreditarconta', methods=['GET', 'POST'])
def professoreditarconta():
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'erro')
        return redirect(url_for('login'))

    if session.get('tipo') != 2:
        flash('Acesso negado. Apenas professores nessa pagina.', 'erro')
        return redirect(url_for('login'))

    idprofessor = session['id_usuario']
    cursor = con.cursor()

    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        telefone = request.form['telefone']
        especialidade = request.form['especialidade']
        senha = request.form['senha']
        confsenha = request.form['confsenha']

        if senha and senha != confsenha:
            flash('As senhas não conferem!', 'erro')
            return render_template('professor-editar-conta.html',
                                   nome=nome, email=email, telefone=telefone, especialidade=especialidade)

        cursor.execute('SELECT 1 FROM usuario WHERE email = ? AND id_usuario != ?', (email, idprofessor))
        if cursor.fetchone():
            flash("Esse email já está cadastrado por outro usuário.", 'erro')
            return redirect(url_for('professoreditarconta'))

        if senha:
            maiusculo = minuscula = numero = caracterEspecial = False
            for s in senha:
                if s.isupper():
                    maiusculo = True
                elif s.islower():
                    minuscula = True
                elif s.isdigit():
                    numero = True
                elif not s.isalnum():
                    caracterEspecial = True

            if not (maiusculo and minuscula and numero and caracterEspecial):
                flash("Sua senha deve ter uma letra maiúscula, uma letra minúscula, um caractere especial e um número.", 'erro')
                return render_template('professor-editar-conta.html', nome=nome, email=email, telefone=telefone, especialidade=especialidade)

            senha_hash = generate_password_hash(senha)
            cursor.execute('UPDATE usuario SET nome = ?, email = ?, telefone = ?, especialidade = ?, senha = ? WHERE id_usuario = ?',
                           (nome, email, telefone, especialidade, senha_hash, idprofessor))
        else:
            cursor.execute('UPDATE usuario SET nome = ?, email = ?, telefone = ?, especialidade = ? WHERE id_usuario = ?',
                           (nome, email, telefone, especialidade, idprofessor))

        con.commit()
        cursor.close()
        flash('Conta atualizada com sucesso!', 'success')
        return redirect(url_for('professordashbord'))

    cursor.execute("SELECT nome, email, telefone, especialidade FROM usuario WHERE id_usuario = ?", (idprofessor,))
    dados = cursor.fetchone()
    cursor.close()

    if not dados:
        flash('Erro ao carregar informações da conta.', 'error')
        return redirect(url_for('professordashbord'))

    nome, email, telefone, especialidade = dados

    return render_template('professor-editar-conta.html', nome=nome, email=email, telefone=telefone, especialidade=especialidade)


@app.route('/professoraulaslista')
def professoraulaslista():
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'erro')
        return redirect(url_for('login'))

    if session.get('tipo') != 2:
        flash('Acesso negado. Apenas professores nessa pagina.', 'erro')
        return redirect(url_for('login'))

    id_professor = session['id_usuario']

    cursor = con.cursor()

    cursor.execute("""
                   SELECT A.ID_AULA,
                          A.NOME,
                          A.DESCRICAO,
                          A.DIA_SEMANA,       -- Índice [3]
                          A.HORARIO,
                          A.HORARIO_FINAL,
                          A.CAPACIDADE,
                          U.NOME AS PROFESSOR,
                          M.MODA,             -- Índice [8] (Corrigido)
                          COUNT(AA.ID_ALUNO) AS VAGAS_OCUPADAS
                   FROM AULA A
                            JOIN USUARIO U ON A.PROFESSOR_ID = U.ID_USUARIO
                            JOIN MODALIDADES M ON A.ID_MODALIDADE = M.ID_MODALIDADE -- Adicionado
                            LEFT JOIN AULA_ALUNO AA ON A.ID_AULA = AA.ID_AULA
                   WHERE A.PROFESSOR_ID = ? -- Filtro do professor (Correto)
                   GROUP BY A.ID_AULA, A.NOME, A.DESCRICAO, A.DIA_SEMANA,
                            A.HORARIO, A.HORARIO_FINAL, A.CAPACIDADE, U.NOME,
                            M.MODA -- Corrigido
                   ORDER BY A.DIA_SEMANA, A.HORARIO
                   """, (id_professor,))

    aulas_db = cursor.fetchall()
    cursor.close()

    aulas_segunda = []
    aulas_terca = []
    aulas_quarta = []
    aulas_quinta = []
    aulas_sexta = []

    for aula in aulas_db:
        dia = aula[3]

        if dia == 1:
            aulas_segunda.append(aula)
        elif dia == 2:
            aulas_terca.append(aula)
        elif dia == 3:
            aulas_quarta.append(aula)
        elif dia == 4:
            aulas_quinta.append(aula)
        elif dia == 5:
            aulas_sexta.append(aula)

    return render_template('professor-aulas-lista.html',
                           titulo='Dashboard professor aulas lista',
                           aulas_segunda=aulas_segunda,
                           aulas_terca=aulas_terca,
                           aulas_quarta=aulas_quarta,
                           aulas_quinta=aulas_quinta,
                           aulas_sexta=aulas_sexta)


@app.route('/professoravisos')
def professoravisos():
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'erro')
        return redirect(url_for('login'))

    if session.get('tipo') != 2:
        flash('Acesso negado. Apenas professores nessa pagina.', 'erro')
        return redirect(url_for('login'))

    cursor = con.cursor()
    cursor.execute("select id_aviso, titulo, descricao from AVISO")
    avisoli = cursor.fetchall()
    cursor.close()

    return render_template('professor-avisos.html', avisoli=avisoli, titulo='Dashboard professor lista aviso')

@app.route('/professoralunosmatriculados/<int:aula_id>')
def professoralunosmatriculados(aula_id):
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'erro')
        return redirect(url_for('login'))

    if session.get('tipo') != 2:
        flash('Acesso negado. Apenas professores nessa pagina', 'erro')
        return redirect(url_for('login'))

    cursor = con.cursor()

    # Pega dados da aula
    cursor.execute("SELECT NOME FROM AULA WHERE ID_AULA = ?", (aula_id,))
    aula = cursor.fetchone()

    # Pega alunos matriculados na aula
    cursor.execute("SELECT U.ID_USUARIO, U.NOME, U.EMAIL FROM AULA_ALUNO AA JOIN USUARIO U ON AA.ID_ALUNO = U.ID_USUARIO WHERE AA.ID_AULA = ?",
                   (aula_id,))
    alunosmatriculado = cursor.fetchall()

    cursor.close()

    return render_template('professor-alunos-matriculados.html', aula=aula, alunosmatriculado=alunosmatriculado, titulo='Dashboard professor alunos matriculados')

@app.route('/cadastrar', methods=['POST'])
def cadastrar():
    nome = request.form['nome']
    email = request.form['email']
    telefone = request.form['telefone']
    senha = request.form['senha']
    confirmar_senha = request.form['confsenha']

    if senha != confirmar_senha:
        flash("As senhas não coincidem", 'error')
        return redirect(url_for('cadastro'))

    maiusculo = minuscula = numero = caracterEspecial = False
    for s in senha:
        if s.isupper():
            maiusculo = True
        elif s.islower():
            minuscula = True
        elif s.isdigit():
            numero = True
        elif not s.isalnum():
            caracterEspecial = True

    if not (maiusculo and minuscula and numero and caracterEspecial):
        flash("Sua senha deve ter uma Letra maiuscula, uma letra minuscula, um caractere especial e um numero")
        return render_template("cadastro.html")

    senha_criptografada = generate_password_hash(senha).decode('utf-8')

    try:
        cursor = con.cursor()
        cursor.execute('SELECT 1 FROM usuario WHERE usuario.email= ?', (email,))
        if cursor.fetchone():
            flash("Esse email já está cadastrado", 'error')
            return redirect(url_for('cadastro'))
        cursor.execute("insert into usuario(nome, email,telefone, senha, tipo,tentativas) values(?,?,?,?,1,0)",
                       (nome, email, telefone, senha_criptografada))
        con.commit()
    finally:
        cursor.close()
    flash("O usuario foi cadastrado com sucesso", 'success')
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'id_usuario' in session:
        flash('Você já está logado.', 'info')  # Mudei de 'erro' para 'info'

        if session.get('tipo') == 1:
            return redirect(url_for('alunodashbord'))
        elif session.get('tipo') == 2:
            return redirect(url_for('professordashbord'))
        else:
            return redirect(url_for('dashbordadmin'))

    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        cursor = con.cursor()

        cursor.execute(
            "SELECT id_usuario, nome, email, telefone, senha, ID_MODALIDADE, tipo, tentativas FROM usuario WHERE email = ?",
            (email,))

        usuario = cursor.fetchone()
        cursor.close()

        if usuario:

            tentativas = usuario[7]

            if tentativas >= 3:
                flash("Sua conta foi bloqueada devido a múltiplas tentativas de login malsucedidas.", 'error')
                return redirect(url_for('login'))

            if check_password_hash(usuario[4], senha):
                flash(f"Login bem-sucedido, {usuario[1]}!", 'success')

                session['id_usuario'] = usuario[0]
                session['nome'] = usuario[1]
                session['tipo'] = usuario[6]

                cursor = con.cursor()
                cursor.execute("UPDATE usuario SET tentativas = 0 WHERE email = ?", (email,))
                con.commit()
                cursor.close()

                tipo_usuario = usuario[6]
                if tipo_usuario == 1:
                    return redirect(url_for('alunodashbord'))
                elif tipo_usuario == 2:
                    return redirect(url_for('professordashbord'))
                else:
                    return redirect(url_for('dashbordadmin'))
            else:
                tentativas += 1
                cursor = con.cursor()
                cursor.execute("UPDATE usuario SET tentativas = ? WHERE email = ?", (tentativas, email))
                con.commit()
                cursor.close()

                flash("E-mail ou senha incorretos.", 'error')
                return redirect(url_for('login'))
        else:
            flash("E-mail ou senha incorretos.", 'error')
            return redirect(url_for('login'))

    return render_template('login.html', titulo='Login')


if __name__ == '__main__':
    app.run(debug=True)