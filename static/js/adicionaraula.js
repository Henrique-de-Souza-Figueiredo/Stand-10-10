const form = document.querySelector('.formulario');
const professorSelect = document.getElementById('professor_id');
const modalidadeInput = document.getElementById('modalidade');

// Função para atualizar o campo modalidade
function atualizarModalidade() {
    const selectedOption = professorSelect.options[professorSelect.selectedIndex];
    modalidadeInput.value = selectedOption.dataset.especialidade || '';
}

// Atualiza modalidade ao carregar a página e ao mudar de professor
professorSelect.addEventListener('change', atualizarModalidade);
atualizarModalidade();

// Prevenir envio se nenhum professor for selecionado
form.addEventListener('submit', function(event) {
    if (professorSelect.value === "") {
        alert("Você precisa selecionar um professor antes de enviar o formulário!");
        professorSelect.focus(); // foca no select
        event.preventDefault(); // impede o envio
    }
});