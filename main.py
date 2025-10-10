from flask import Flask, render_template, flash, request, url_for, redirect, session
from flask_bcrypt import generate_password_hash, check_password_hash
import fdb

app = Flask(__name__)

app.config['SECRET_KEY'] = 'senhastandsi,teacademia'

host = 'localhost'
database = r'C:\Users\Aluno\Downloads\BANCO (1)\BANCO.FDB'
user = 'sysdba'
password = 'sysdba'

con = fdb.connect(host=host, database=database, user=user, password=password)


@app.route('/')
def index():
    return render_template('index.html', titulo='Pagina inicial')


@app.route('/cadastro')
def cadastro():
    return render_template('cadastro.html', titulo='Novo usuario')


@app.route('/alunodashbord')
def alunodashbord():
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'erro')
        return redirect(url_for('login'))

    if session.get('tipo') != 1:
        flash('Acesso negado. Somente administradores podem editar contas.', 'erro')
        return redirect(url_for('login'))
    return render_template('aluno-dashbord.html', titulo='Dashboard aluno')

@app.route('/alunoprofessoreslista')
def alunoprofessoreslista():
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'erro')
        return redirect(url_for('login'))

    if session.get('tipo') != 1:
        flash('Acesso negado. Somente administradores podem editar contas.', 'erro')
        return redirect(url_for('login'))

    cursor = con.cursor()
    cursor.execute("select id_usuario, nome, email, especialidade from USUARIO WHERE tipo = 2")
    profli = cursor.fetchall()
    cursor.close()
    return render_template('aluno-professores-lista.html', profli=profli, titulo='Dashboard aluno lista professor')

@app.route('/alunoavisos')
def alunoavisos():
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'erro')
        return redirect(url_for('login'))

    if session.get('tipo') != 1:
        flash('Acesso negado. Somente administradores podem editar contas.', 'erro')
        return redirect(url_for('login'))

    cursor = con.cursor()
    cursor.execute("select id_aviso, titulo, descricao from AVISO")
    avisoli = cursor.fetchall()
    cursor.close()

    return render_template('aluno-avisos.html', avisoli=avisoli, titulo='Dashboard aluno lista aviso')


@app.route('/alunoaulaslista')
def alunoaulaslista():
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'erro')
        return redirect(url_for('login'))

    if session.get('tipo') != 1:
        flash('Acesso negado. Somente administradores podem editar contas.', 'erro')
        return redirect(url_for('login'))
    return render_template('aluno-aulas-lista.html', titulo='Dashboard aluno')

@app.route('/alunoeditarconta', methods=['GET', 'POST'])
def alunoeditarconta():
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'erro')
        return redirect(url_for('login'))

    if session.get('tipo') != 1:
        flash('Acesso negado. Somente aluno.', 'erro')
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
        flash('Acesso negado. Somente administradores podem editar contas.', 'erro')
        return redirect(url_for('login'))

    cursor = con.cursor()

    cursor.execute("SELECT COUNT(*) FROM usuario WHERE tipo = 1")
    total_alunos = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM usuario WHERE tipo = 2")
    total_professores = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM usuario WHERE tipo = 3")
    total_admins = cursor.fetchone()[0]

    cursor.close()

    return render_template('dashbord-admin.html', titulo='Dashboard Admin', total_alunos=total_alunos, total_professores=total_professores,total_admins=total_admins)


@app.route('/adminalunoslista')
def adminalunoslista():
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'erro')
        return redirect(url_for('login'))

    if session.get('tipo') != 3:
        flash('Acesso negado. Somente administradores podem editar contas.', 'erro')
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
        flash('Acesso negado. Somente administradores podem editar contas.', 'erro')
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
        flash('Acesso negado. Somente administradores podem editar contas.', 'erro')
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
        flash('Acesso negado. Somente administradores podem excluir contas.', 'erro')
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
        flash('Acesso negado. Somente administradores podem editar contas.', 'erro')
        return redirect(url_for('login'))

    cursor = con.cursor()
    cursor.execute("select id_usuario, nome, email, tentativas  from USUARIO WHERE tipo = 2")
    profli = cursor.fetchall()
    cursor.close()
    return render_template('admin-professores-lista.html', profli=profli, titulo='Dashboard admin lista professores')


@app.route('/admineditarprofessor/<int:id>', methods=['GET', 'POST'])
def admineditarprofessor(id):
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'erro')
        return redirect(url_for('login'))

    if session.get('tipo') != 3:  # tipo 3 = admin
        flash('Acesso negado. Somente administradores podem editar contas.', 'erro')
        return redirect(url_for('login'))

    cursor = con.cursor()
    cursor.execute("SELECT nome, email, telefone, especialidade, senha FROM usuario WHERE id_usuario = ?", (id,))
    usuario = cursor.fetchone()

    if not usuario:
        cursor.close()
        flash("Usuário não foi encontrado.", 'erro')
        return redirect(url_for('adminprofessoreslista'))

    nome, email, telefone, especialidade, senha_atual = usuario

    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        telefone = request.form['telefone']
        especialidade = request.form['especialidade']
        senha = request.form['senha']
        confsenha = request.form['confsenha']

        if senha and senha != confsenha:
            flash('As senhas não conferem!', 'erro')
            return render_template("admin-editar-professor.html", id=id, nome=nome, email=email, telefone=telefone, especialidade=especialidade)

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
                return render_template("admin-editar-professor.html",id=id, nome=nome, email=email, telefone=telefone, especialidade=especialidade)

            senha_hash = generate_password_hash(senha)
            cursor.execute('UPDATE usuario SET nome = ?, email = ?, telefone = ?, especialidade = ?, senha = ? WHERE id_usuario = ?',
                           (nome, email, telefone, especialidade, senha_hash, id))
        else:
            cursor.execute('UPDATE usuario SET nome = ?, email = ?, telefone = ?, especialidade = ? WHERE id_usuario = ?',
                           (nome, email, telefone, especialidade, id))

        con.commit()
        cursor.close()
        flash('Usuário atualizado com sucesso!', 'success')
        return redirect(url_for('adminprofessoreslista'))

    cursor.close()
    return render_template(
        'admin-editar-professor.html',id=id, nome=nome, email=email, telefone=telefone, especialidade=especialidade)


@app.route('/adminexcluirprofessor/<int:id>', methods=['GET', 'POST'])
def adminexcluirprofessor(id):
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'erro')
        return redirect(url_for('login'))

    if session.get('tipo') != 3:
        flash('Acesso negado. Somente administradores podem excluir contas.', 'erro')
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
            cursor.execute("DELETE FROM usuario WHERE id_usuario = ?", (id,))
            con.commit()
            cursor.close()
            flash(f"O professor '{nome}' foi excluído com sucesso.", 'success')
            return redirect(url_for('adminprofessoreslista'))
        else:
            cursor.close()
            flash("Exclusão cancelada.", 'erro')
            return redirect(url_for('adminprofessoreslista'))

    cursor.close()
    return render_template('admin-excluir-professor.html', id=id, nome=nome, email=email)


@app.route('/adminadmlista')
def adminadmlista():
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'erro')
        return redirect(url_for('login'))

    if session.get('tipo') != 3:
        flash('Acesso negado. Somente administradores podem acessar essa página.', 'erro')
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
        flash('Acesso negado. Somente administradores podem editar contas.', 'erro')
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
        flash('Acesso negado. Somente administradores podem excluir contas.', 'erro')
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
        flash('Acesso negado. Somente administradores podem adicionar usuários.', 'erro')
        return redirect(url_for('login'))

    if request.method == 'POST':
        tipo = int(request.form['tipos'])
        nome = request.form['nome']
        email = request.form['email']
        telefone = request.form['telefone']
        especialidade = request.form.get('especialidade', '')
        senha = request.form['senha']
        confsenha = request.form['confsenha']

        cursor = con.cursor()

        try:
            cursor.execute("SELECT id_usuario FROM usuario WHERE email = ?", (email,))
            if cursor.fetchone():
                flash("Este email já está cadastrado!", 'erro')
                return render_template('admin-adicionar-usuario.html',
                                       nome=nome, email=email, telefone=telefone,
                                       especialidade=especialidade, tipos=tipo)

            if senha != confsenha:
                flash('As senhas não conferem!', 'erro')
                return render_template('admin-adicionar-usuario.html',
                                       nome=nome, email=email, telefone=telefone,
                                       especialidade=especialidade, tipos=tipo)

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
                flash("Sua senha deve conter letra maiúscula, minúscula, número e caractere especial.", 'erro')
                return render_template('admin-adicionar-usuario.html',
                                       nome=nome, email=email, telefone=telefone,
                                       especialidade=especialidade, tipos=tipo)

            senha_hash = generate_password_hash(senha)

            if tipo == 2:
                cursor.execute("INSERT INTO usuario (nome, email, telefone, especialidade, senha, tipo, tentativas) VALUES (?, ?, ?, ?, ?, ?, 0)",
                               (nome, email, telefone, especialidade, senha_hash, tipo))
            else:
                cursor.execute("INSERT INTO usuario (nome, email, telefone, senha, tipo, tentativas)VALUES (?, ?, ?, ?, ?, 0)",
                               (nome, email, telefone, senha_hash, tipo))

            con.commit()
            flash('Usuário cadastrado com sucesso!', 'success')
            return redirect(url_for('dashbordadmin'))

        finally:
            cursor.close()

    return render_template('admin-adicionar-usuario.html')


@app.route('/adminaulaslista')
def adminaulaslista():
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'erro')
        return redirect(url_for('login'))

    if session.get('tipo') != 3:
        flash('Acesso negado. Somente administradores podem editar contas.', 'erro')
        return redirect(url_for('login'))
    return render_template('admin-aulas-listas.html', titulo='Dashboard admin aulas lista')


@app.route('/adminadicionaraula')
def adminadicionaraula():
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'erro')
        return redirect(url_for('login'))

    if session.get('tipo') != 3:
        flash('Acesso negado. Somente administradores podem editar contas.', 'erro')
        return redirect(url_for('login'))
    return render_template('admin-adicionar-aula.html', titulo='Dashboard admin adicionar aula')


@app.route('/adminalunosmatriculados')
def adminalunosmatriculados():
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'erro')
        return redirect(url_for('login'))

    if session.get('tipo') != 3:
        flash('Acesso negado. Somente administradores podem editar contas.', 'erro')
        return redirect(url_for('login'))
    return render_template('admin-alunos-matriculados.html', titulo='Dashboard admin alunos matriculados')


@app.route('/adminmatricularaluno')
def adminmatricularaluno():
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'erro')
        return redirect(url_for('login'))

    if session.get('tipo') != 3:
        flash('Acesso negado. Somente administradores podem editar contas.', 'erro')
        return redirect(url_for('login'))
    return render_template('admin-matricular-aluno.html', titulo='Dashboard admin matricular aluno')


@app.route('/adminexcluiralunoaula')
def adminexcluiralunoaula():
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'erro')
        return redirect(url_for('login'))

    if session.get('tipo') != 3:
        flash('Acesso negado. Somente administradores podem editar contas.', 'erro')
        return redirect(url_for('login'))
    return render_template('admin-excluir-aluno-aula.html', titulo='Dashboard admin excluir aluno aula')


@app.route('/admineditaraula')
def admineditaraula():
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'erro')
        return redirect(url_for('login'))

    if session.get('tipo') != 3:
        flash('Acesso negado. Somente administradores podem editar contas.', 'erro')
        return redirect(url_for('login'))
    return render_template('admin-editar-aula.html', titulo='Dashboard admin editar aula')


@app.route('/adminexcluiraula')
def adminexcluiraula():
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'erro')
        return redirect(url_for('login'))

    if session.get('tipo') != 3:
        flash('Acesso negado. Somente administradores podem editar contas.', 'erro')
        return redirect(url_for('login'))
    return render_template('admin-excluir-aula.html', titulo='Dashboard admin excluir aula')


@app.route('/adminavisos')
def adminavisos():
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'erro')
        return redirect(url_for('login'))

    if session.get('tipo') != 3:
        flash('Acesso negado. Somente administradores podem editar contas.', 'erro')
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
        flash('Acesso negado. Somente administradores podem editar contas.', 'erro')
        return redirect(url_for('login'))

    if request.method == 'POST':
        titulo = request.form['titulo']
        descricao = request.form['descricao']

        cursor = con.cursor()
        cursor.execute("INSERT INTO aviso (titulo, descricao) VALUES (?, ?)", (titulo, descricao))
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
        flash('Acesso negado. Somente administradores podem editar contas.', 'erro')
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
    if 'id_usuario' not in session or session.get('tipo') != 3:
        flash('Acesso negado.', 'erro')
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

    if session.get('tipo') != 3:  #
        flash('Acesso negado. Somente administradores podem editar contas.', 'erro')
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
        flash('Acesso negado. Apenas professores podem editar sua conta.', 'erro')
        return redirect(url_for('login'))
    return render_template('professor-dashbord.html', titulo='Dashboard professor')

@app.route('/professoreditarconta', methods=['GET', 'POST'])
def professoreditarconta():
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'erro')
        return redirect(url_for('login'))

    if session.get('tipo') != 2:
        flash('Acesso negado. Apenas professores podem editar sua conta.', 'erro')
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

    return render_template('professor-editar-conta.html',nome=nome, email=email, telefone=telefone, especialidade=especialidade)

@app.route('/professoraulaslista')
def professoraulaslista():
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'erro')
        return redirect(url_for('login'))

    if session.get('tipo') != 2:
        flash('Acesso negado. Apenas professores podem editar sua conta.', 'erro')
        return redirect(url_for('login'))
    return render_template('professor-aulas-lista.html', titulo='Dashboard professor aulas lista')

@app.route('/professoravisos')
def professoravisos():
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'erro')
        return redirect(url_for('login'))

    if session.get('tipo') != 2:
        flash('Acesso negado. Apenas professores podem editar sua conta.', 'erro')
        return redirect(url_for('login'))

    cursor = con.cursor()
    cursor.execute("select id_aviso, titulo, descricao from AVISO")
    avisoli = cursor.fetchall()
    cursor.close()

    return render_template('professor-avisos.html', avisoli=avisoli, titulo='Dashboard professor lista aviso')

@app.route('/professoralunosmatriculados')
def professoralunosmatriculados():
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'erro')
        return redirect(url_for('login'))

    if session.get('tipo') != 2:
        flash('Acesso negado. Apenas professores podem editar sua conta.', 'erro')
        return redirect(url_for('login'))
    return render_template('professor-alunos-matriculados.html', titulo='Dashboard professor alunos matriculados')

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
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        cursor = con.cursor()
        cursor.execute(
            "SELECT id_usuario, nome, email, telefone, senha, especialidade, tipo, tentativas FROM usuario WHERE email = ?",
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