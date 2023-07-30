(function() {
  $(document).ready(function() {
    var itemsTable = $('#items-table').DataTable();

    function refreshTable() {
      $.getJSON('/get_equipment', function(data) {
        if (Array.isArray(data)) {
          itemsTable.clear();
          data.forEach(function(item) {
            itemsTable.row.add([
              item.name,
              item.type,
              '<button data-item-id="' + item.id + '" class="signout-item-btn">Sign out</button>'
            ]);
          });
          itemsTable.draw();
        } else {
          console.log(data.message);
        }
      });
    }

    $(document).on('click', '.signout-item-btn', function() {
      var itemId = $(this).data('item-id');
      var row = $(this).closest('tr');
      $.ajax({
        url: '/equipment',
        type: 'POST',
        data: {
          item_id: itemId,
        },
        success: function(response) {
          alert('Item signed out successfully');
          row.remove();
        },
        error: function(error) {
          alert('Failed to sign out item');
        }
      });
    });

    refreshTable();
  });
})();