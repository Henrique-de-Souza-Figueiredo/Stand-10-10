const btnMenu = document.getElementById('btnMenu');
const menuMobile = document.getElementById('menuMobile');
const header = document.querySelector('.cabecalho-principal');

btnMenu.addEventListener('click', function () {
    menuMobile.classList.toggle('aberto');
    header.classList.toggle('menu-aberto');
});

const btnMenuDash = document.getElementById('btnMenuDash');
const menuMobileDash = document.getElementById('menuMobileDash');
const headerDash = document.querySelector('.cabecalho-principal');

if (btnMenuDash && menuMobileDash && headerDash) {
    btnMenuDash.addEventListener('click', function () {
        menuMobileDash.classList.toggle('aberto-dash');
        headerDash.classList.toggle('menu-aberto-dash');
    });
}



function inscrever(botao) {
    const itemAula = botao.closest('.lista-item');

    let vagasOcupadas = parseInt(itemAula.dataset.vagasOcupadas);
    const vagasMaximas = parseInt(itemAula.dataset.vagasMaximas);

    const pVagas = itemAula.querySelector('.vagas-info');

    const estaInscrito = botao.classList.contains('inscrito');

    if (!estaInscrito) {
        if (vagasOcupadas < vagasMaximas) {
            vagasOcupadas++;

            botao.textContent = "Inscrito";
            botao.style.backgroundColor = "#2E9F2E";
            botao.classList.add('inscrito');
        } else {
            alert("Não há mais vagas disponíveis para esta aula.");
        }
    } else {
        vagasOcupadas--;

        botao.textContent = "Inscrever";
        botao.style.backgroundColor = "#36DB36";
        botao.classList.remove('inscrito');
    }

    itemAula.dataset.vagasOcupadas = vagasOcupadas;
    pVagas.textContent = `(${vagasOcupadas}/${vagasMaximas})`;
}


