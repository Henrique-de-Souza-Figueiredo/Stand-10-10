
    var allProfessores = {{ professores|tojson }};

    var modalidadeSelect = document.getElementById('modalidade-select');
    var professorSelect = document.getElementById('professor-select');
    var capacidadeInput = document.getElementById('capacidade-input');

    modalidadeSelect.addEventListener('change', function() {

        var selectedModalidadeId = this.value;

        var selectedOption = this.options[this.selectedIndex];

        professorSelect.innerHTML = '';

        if (selectedModalidadeId) {

            capacidadeInput.value = selectedOption.getAttribute('data-vagas');
            capacidadeInput.readOnly = true;

            professorSelect.disabled = false;
            professorSelect.add(new Option('Selecione um professor', ''));

            allProfessores.forEach(function(professor) {

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
</script>