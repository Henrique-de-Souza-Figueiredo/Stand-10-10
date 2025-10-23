const form = document.querySelector('.formulario');
const dataInput = document.querySelector('input[name="data_aula"]');
const horarioInicio = document.querySelector('input[name="horario"]');
const horarioFinal = document.querySelector('input[name="horario_final"]');

form.addEventListener('submit', (event) => {
  const hoje = new Date();
  const dataSelecionada = new Date(dataInput.value + "T00:00");
  const horarioInicioValor = horarioInicio.value;
  const horarioFinalValor = horarioFinal.value;

  const hojeSemHora = new Date(hoje.getFullYear(), hoje.getMonth(), hoje.getDate());

  // Impede data passada
  if (dataSelecionada < hojeSemHora) {
    alert("A data da aula não pode ser no passado!");
    event.preventDefault();
    return;
  }

  // Impede horário final menor ou igual ao inicial
  if (horarioFinalValor <= horarioInicioValor) {
    alert("O horário de término deve ser maior que o horário de início!");
    event.preventDefault();
    return;
  }

  const horarioMin = "07:00";
  const horarioMax = "22:00";

  // Valida intervalo de horários permitidos
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
