// Selecionar elementos (Adicionar o capacidadeInput)
const form = document.querySelector('.formulario');
const professorSelect = document.getElementById('professor_id');
const modalidadeInput = document.getElementById('modalidade');
const capacidadeInput = document.getElementById('capacidade'); // <-- ADICIONAR ESTA LINHA
const dataInput = document.querySelector('input[name="data_aula"]');
const horarioInicio = document.querySelector('input[name="horario"]');
const horarioFinal = document.querySelector('input[name="horario_final"]');

// Atualiza automaticamente os campos "modalidade" E "capacidade"
professorSelect.addEventListener('change', () => {
  const selectedOption = professorSelect.options[professorSelect.selectedIndex];

  // Atualiza modalidade
  modalidadeInput.value = selectedOption.dataset.especialidade || '';

  // ATUALIZAR: Adiciona a lógica para capacidade
  capacidadeInput.value = selectedOption.dataset.capacidade || '';
});

// Validação antes de enviar o formulário (SEU CÓDIGO ORIGINAL, ESTÁ CORRETO)
form.addEventListener('submit', (event) => {
  const hoje = new Date();
  const dataSelecionada = new Date(dataInput.value + "T00:00");
  const horarioInicioValor = horarioInicio.value;
  const horarioFinalValor = horarioFinal.value;


  if (professorSelect.value === "") {
    alert("Por favor, selecione um professor antes de continuar!");
    event.preventDefault();
    return;
  }

  const hojeSemHora = new Date(hoje.getFullYear(), hoje.getMonth(), hoje.getDate());
  if (dataSelecionada < hojeSemHora) {
    alert("A data da aula não pode ser no passado!");
    event.preventDefault();
    return;
  }

  if (horarioFinalValor <= horarioInicioValor) {
    alert("O horário de término deve ser maior que o horário de início!");
    event.preventDefault();
    return;
  }

  const horarioMin = "07:00";
  const horarioMax = "22:00";

  if (horarioInicioValor < horarioMin || horarioInicioValor > horarioMax) {
    alert("O horário de início deve estar entre 07:00 e 22:00!");
    event.preventDefault();
    return;
  }

  if (horarioFinalValor < horarioMin || horarioFinalValor > horarioMax) {
    alert("O horário de término deve estar entre 07:00 e 22:00!");
    event.preventDefault();
    return;
  }

});