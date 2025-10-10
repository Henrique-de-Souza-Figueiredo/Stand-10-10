        document.addEventListener('DOMContentLoaded', function () {

            const tipoSelecao = document.getElementById('tipo-selecao');
            const tituloFormulario = document.querySelector('.formulario h1');
            const campoEspecialidade = document.getElementById('campo-especialidade');

            function atualizarFormulario() {
                const tipoEscolhido = tipoSelecao.value;

                if (tipoEscolhido === '1') {
                    tituloFormulario.textContent = 'Adicionar Aluno';
                    campoEspecialidade.style.display = 'none';

                } else if (tipoEscolhido === '2') {
                    tituloFormulario.textContent = 'Adicionar Professor';
                    campoEspecialidade.style.display = 'block';

                } else if (tipoEscolhido === '3') {
                    tituloFormulario.textContent = 'Adicionar Admin';
                    campoEspecialidade.style.display = 'none';

                } else {
                    tituloFormulario.textContent = 'Adicionar Usuário';
                    campoEspecialidade.style.display = 'none';
                }


            }

            tipoSelecao.addEventListener('change', atualizarFormulario);

            atualizarFormulario();
        });