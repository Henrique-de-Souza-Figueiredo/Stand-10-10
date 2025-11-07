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

function gerarRelatorio(selectElement) {

    var url = selectElement.value;

    if (url) {
        window.location.href = url;

        selectElement.selectedIndex = 0;
    }
}




