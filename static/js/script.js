var btnUpload = $("#upload_file"),
    btnOuter = $(".button_outer");

// Hide the result table-container initially
$(".table-container").hide();

btnUpload.on("change", function (e) {
    var ext = btnUpload.val().split('.').pop().toLowerCase();
    if ($.inArray(ext, ['gif', 'png', 'jpg', 'jpeg']) == -1) {
        $(".error_msg").text("Not an Image...");
        // Clear the input field
        btnUpload.val('');
    } else {
        $(".error_msg").text("");
        btnOuter.addClass("file_uploading");

        // Create a FormData object to send the file to the server
        var formData = new FormData();
        formData.append("file", e.target.files[0]);

        // Make an AJAX POST request to the Flask server
        $.ajax({
            url: "/",  // Replace with the actual URL of your Flask endpoint
            type: "POST",
            data: formData,
            processData: false,
            contentType: false,
            success: function (response) {
                if (response.error) {
                    // Handle error responses
                    $(".error_msg").text(response.error);
                    btnOuter.removeClass("file_uploading");
                } else {
                    // Handle successful JSON response
                    // Display the uploaded image
                    var uploadedFile = URL.createObjectURL(e.target.files[0]);
                    setTimeout(function () {
                        $("#uploaded_view").append('<img src="' + uploadedFile + '" />').addClass("show");
                        
                        // Show the result table-container after displaying the image
                        $(".table-container").show();
                    }, 0);

                    // Display the image name
                    $("#image_name").text("Test Image: " + response.image_name);

                    // Display the classification results table
                    $("#result_table tbody").empty(); // Clear previous results
                    $.each(response.zipped_data, function (index, item) {
                        $("#result_table tbody").append(
                            '<tr><td>' + item[0] + '</td><td>' + item[1] + '</td></tr>'
                        );
                    });

                    // Show the success message
                    btnOuter.addClass("file_uploaded");

                    // Clear the input field after successful upload
                    btnUpload.val('');
                }
            },
            error: function () {
                $(".error_msg").text("An error occurred while processing the image.");
                btnOuter.removeClass("file_uploading");
            },
        });
    }
});

$(".file_remove").on("click", function (e) {
    // Clear the UI when removing the uploaded image
    $("#uploaded_view").removeClass("show");
    $("#uploaded_view").find("img").remove();
    btnOuter.removeClass("file_uploading");
    btnOuter.removeClass("file_uploaded");

    // Clear the input field
    btnUpload.val('');

    // Clear the image name and classification results
    $("#image_name").text("");

    // Hide the result table-container
    $(".table-container").hide();
    $("#result_table tbody").empty(); // Clear previous results
});