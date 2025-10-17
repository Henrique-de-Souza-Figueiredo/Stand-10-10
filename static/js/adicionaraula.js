const form = document.querySelector('.formulario');
const professorSelect = document.getElementById('professor_id');
const modalidadeInput = document.getElementById('modalidade');
const dataInput = document.querySelector('input[name="data_aula"]');
const horarioInicio = document.querySelector('input[name="horario"]');
const horarioFinal = document.querySelector('input[name="horario_final"]');

// Atualiza automaticamente o campo "modalidade" conforme o professor selecionado
professorSelect.addEventListener('change', () => {
  const selectedOption = professorSelect.options[professorSelect.selectedIndex];
  modalidadeInput.value = selectedOption.dataset.especialidade || '';
});

// Validação antes de enviar o formulário
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

  // 2️⃣ Impede datas passadas
  const hojeSemHora = new Date(hoje.getFullYear(), hoje.getMonth(), hoje.getDate());
  if (dataSelecionada < hojeSemHora) {
    alert("A data da aula não pode ser no passado!");
    event.preventDefault();
    return;
  }

  // 3️⃣ Impede horário final menor ou igual ao horário inicial
  if (horarioFinalValor <= horarioInicioValor) {
    alert("O horário de término deve ser posterior ao horário de início!");
    event.preventDefault();
    return;
  }

    // 4️⃣ Impede horários fora do intervalo permitido (07:00 - 22:00)
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