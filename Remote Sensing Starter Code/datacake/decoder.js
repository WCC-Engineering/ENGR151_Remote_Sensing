// decoder.js -- Datacake HTTP payload decoder for the ENGR 151 connected sensor.
// OWNER: telemetry
//
// Paste this whole file into Datacake: your device > Configuration >
// HTTP Payload Decoder. Datacake runs it every time Notehub forwards a message.
//
// What it does with each Notehub message:
//   1. Ignores anything that is not one of your samples (file other than data.qo).
//   2. Sends each field to the Datacake field with the same name in CAPITALS
//      (data1 goes to DATA1).
//   3. Treats a field that is absent as 0 or false. LoRa templates leave out
//      fields whose value is 0 or false, so "absent" really means zero.
//   4. Skips -9999, which means "no valid reading", so it never reaches a chart.
//   5. Stamps each value with the time it was measured, not when it arrived.

// EDIT THIS LIST to match telemetry.DATA_FIELDS: the same names, and the type
// "number" for any number or "boolean" for True/False.
var DATA_FIELDS = {
    data1: "number",
    data2: "number",
    data3: "number",
    data4: "number",
    data5: "boolean"
};

// Nothing below this line needs to change. If you run into errors, ask your
// instructor or lab tech.
var DATA_NOTEFILE = "data.qo";
var MISSING = -9999;

function Decoder(request) {
    var event = JSON.parse(request.body);
    if (event.file !== DATA_NOTEFILE) {
        return [];
    }

    var body = event.body || {};
    var device = event.device;          // Notecard ID, e.g. "dev:0080e1150045224b"
    var time = event.when || event.received;
    var results = [];

    for (var name in DATA_FIELDS) {
        var value = body[name];
        if (value === undefined || value === null) {
            value = (DATA_FIELDS[name] === "boolean") ? false : 0;
        }
        if (DATA_FIELDS[name] === "number" && value <= MISSING) {
            continue;
        }
        var item = { device: device, field: name.toUpperCase(), value: value };
        if (time) {
            item.timestamp = Math.floor(time);
        }
        results.push(item);
    }
    return results;
}
