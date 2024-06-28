$(document).ready(function() {
  $(".search").keyup(function () {
    var searchTerm = $(".search").val();
    var listItem = $('.results tbody').children('tr');
    var searchSplit = searchTerm.replace(/ /g, "'):containsi('")

  $.extend($.expr[':'], {'containsi': function(elem, i, match, array){
        return (elem.textContent || elem.innerText || '').toLowerCase().indexOf((match[3] || "").toLowerCase()) >= 0;
    }
  });

  $(".results tbody tr").not(":containsi('" + searchSplit + "')").each(function(e){
    $(this).attr('visible','false');
  });

  $(".results tbody tr:containsi('" + searchSplit + "')").each(function(e){
    $(this).attr('visible','true');
  });

  var jobCount = $('.results tbody tr[visible="true"]').length;
    $('.counter').text(jobCount + ' элементов');

  if(jobCount == '0') {$('.no-result').show();}
    else {$('.no-result').hide();}
		  });
});

////$(document).ready( function () {
////    $('#example').DataTable();
////    $('example').dataTable({searching: false, paging: false, info: false});
////} );
$(document).ready( function () {
new DataTable('#example', {
    searching: false,
    info: false,
     "pageLength": 25,
     "language": {
      "lengthMenu": "Количество на странице  _MENU_"
   }
});
$("#example").bootstrapTable("hideLoading");
});


//
//var exampleModal = document.getElementById('modal_users')
//exampleModal.addEventListener('show.bs.modal', function (event) {
//  // Button that triggered the modal
//  var button = event.relatedTarget
//  var recipient = button.getAttribute('data-bs-whatever')
//  var modalBodyInput = exampleModal.querySelector('.modal-body input')
//  modalBodyInput.value = recipient
//})
//
//
//
