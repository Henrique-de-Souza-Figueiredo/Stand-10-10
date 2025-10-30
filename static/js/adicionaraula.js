// Garante que o script só rode depois que o HTML (e a variável) carregar
document.addEventListener('DOMContentLoaded', function () {

    // A variável 'allProfessores' foi criada no HTML.
    // Este script já tem acesso a ela.

    // 1. Pega os elementos
    var modalidadeSelect = document.getElementById('modalidade-select');
    var professorSelect = document.getElementById('professor-select');
    var capacidadeInput = document.getElementById('capacidade-input');

    // 2. Adiciona o "ouvinte"
    modalidadeSelect.addEventListener('change', function () {

        var selectedModalidadeId = this.value;
        var selectedOption = this.options[this.selectedIndex];

        professorSelect.innerHTML = ''; // Limpa o dropdown

        if (selectedModalidadeId) {
            // 3. Preenche Vagas
            capacidadeInput.value = selectedOption.getAttribute('data-vagas');
            capacidadeInput.readOnly = true;

            // 4. Habilita Professores
            professorSelect.disabled = false;
            professorSelect.add(new Option('Selecione um professor', ''));

            // 5. Filtra (usando a variável 'allProfessores' que o HTML criou)
            allProfessores.forEach(function (professor) {
                if (professor[2] == selectedModalidadeId) {
                    var option = new Option(professor[1], professor[0]);
                    professorSelect.add(option);
                }
            });

        } else {
            capacidadeInput.value = '';
            capacidadeInput.placeholder = 'Vagas (automático)';
            capacidadeInput.readOnly = true;

            professorSelect.disabled = true;
            professorSelect.add(new Option('Selecione a modalidade primeiro', ''));
        }
    });
});