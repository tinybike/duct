/**
 * duct front-end core
 */
(function ($) {

    // Create modal alert windows (using Foundation reveal)
    function modal_alert(bodytext, bodytag, headertext) {
        var modal_body;
        if (headertext) {
            $('#modal-header').empty().text(headertext);
        }
        if (bodytext) {
            modal_body = (bodytag) ? $('<' + bodytag + ' />') : $('<p />');
            $('#modal-body').empty().append(
                modal_body.addClass('modal-error-text').text(bodytext)
            );
        }
        $('#modal-ok-box').show();
        $('#modal-dynamic').foundation('reveal', 'open');
    }
    function modal_prompt(prompt, bodytag, headertext) {
        var modal_body;
        if (headertext) {
            $('#modal-header').empty().html(headertext);
        }
        if (prompt) {
            modal_body = (bodytag) ? $('<' + bodytag + ' />') : $('<p />');
            $('#modal-body').empty().append(
                modal_body
                    .addClass('modal-error-text')
                    .append(prompt)
            );
        }
        $('#modal-dynamic').foundation('reveal', 'open');
    }

    function Duct(socket) {
        this.socket = socket;
    }

    // Get all active votes
    Duct.prototype.sync = function () {
        this.socket.emit('sync');
    };
    
    Duct.prototype.intake = function () {
        var self = this;
        this.socket.on('synced', function (res) {
            console.log(res);
        });
        this.socket.on('contract-created', function (res) {
            if (res && res.address) {
                $('#contract-address-input').val(res.address);
                if (res.functions) {
                    var html = "<select>";
                    for (var i = 0, len = res.functions.length; i < len; ++i) {
                        html += "<option>" + res.functions[i] + "</option>";
                    }
                    html += "</select>";
                    $('#functions-input-label').show();
                    $('#functions-input').html(html);
                }
            } else {
                console.log("Error creating contract:", res);
            }
        });
        this.socket.on('contract-output', function (res) {
            if (res && res.reputation && res.outcomes && res.reporter_bonus) {
                $('#status-receiver').slideUp('slow');
                var reputation = "Reputation: " + JSON.stringify(res.reputation, null, 3) + "\n";
                var output = $('<pre />').text(reputation + outcomes + reporter_bonus);
                $('#main-receiver').append(output).show();
            } else {
                $('#status-receiver').html("<h4>Contract execution unsuccessful</h4>");
            }
        });
        return this;
    };

    Duct.prototype.exhaust = function () {
        var self = this;

        $('#modal-ok-button').click(function (event) {
            event.preventDefault();
            $('#modal-ok-box').hide();
            $('#modal-dynamic').foundation('reveal', 'close');
        });

        $('#create-contract').click(function (event) {
            event.preventDefault();
            var prompt = '<hr /><div class="row centered">' +
                         '<form action="#" method="POST" id="create-contract-form">' +
                         '<textarea id="contract-source" />' +
                         '<hr />' +
                         '<button type="submit" class="button expand" '+
                         'id="create-contract-button">Create</button>' +
                         '</form></div>';
            modal_prompt(prompt, "h2", "Create contract");
            $('#create-contract-form').submit(function (event) {
                event.preventDefault();
                var source = $('#contract-source').val();
                if (source == "") {
                    source = "def main(a,b):\n"+
                             "    return(a^b)";
                }
                self.socket.emit('create-contract', {
                    source: source,
                    gas_input: 70000000
                });
                this.reset();
                $('#modal-dynamic').foundation('reveal', 'close');
            });
        });

        $('form#compile-contract').submit(function (event) {
            event.preventDefault();
            // c305c901078781c232a2a521c2af7980f8385ee9
        });

        $('form#run-contract-form').submit(function (event) {
            event.preventDefault();
            $('#status-receiver').html('<h4>Running contract...</h4>').show();
            var data = {
                contract_address: $('#contract-address-input').val(),
                gas_input: parseInt($('#gas-input').val()),
                function_name: $('#function-name-input').val()
            };
            self.socket.emit('run-contract', data);
            this.reset();
        });

        return self;
    };

    $(document).ready(function () {
        var socket_url, duct;
        socket_url = window.location.protocol + '//' + document.domain +
            ':' + location.port + '/socket.io/';
        socket = io.connect(socket_url);
        socket.on('connect', function () {
            duct = new Duct(socket);
            duct.intake().exhaust();
        })
    });

})(jQuery);
