package cu.soklar.sms_bridge

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.provider.Telephony
import android.util.Log
import org.json.JSONObject
import java.io.File
import kotlin.random.Random

/**
 * Recibe SMS y deja un JSON en files/inbox/ para que Flet lo lea.
 * No envía HTTP: de eso se encarga Flet (cola de reintentos).
 */
class SmsReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action != Telephony.Sms.Intents.SMS_RECEIVED_ACTION) return
        val bundle: Bundle = intent.extras ?: return
        @Suppress("UNCHECKED_CAST")
        val pdus = bundle.get("pdus") as? Array<Any> ?: return
        val format = bundle.getString("format") ?: "3gpp"

        val sb = StringBuilder()
        var sender = ""
        for (pdu in pdus) {
            val msg = android.telephony.SmsMessage.createFromPdu(pdu as ByteArray, format) ?: continue
            if (sender.isEmpty()) sender = msg.originatingAddress ?: ""
            sb.append(msg.messageBody)
        }
        val cuerpo = sb.toString()
        if (cuerpo.isBlank()) return
        Log.d("SOKLAR-SMS", "De $sender: ${cuerpo.take(120)}")

        // Guardar JSON en el directorio privado de la app
        val dir = File(context.filesDir, "inbox").apply { mkdirs() }
        val name = "${System.currentTimeMillis()}_${Random.nextInt(1_000_000)}.json"
        val obj = JSONObject().apply {
            put("remitente", sender)
            put("cuerpo", cuerpo)
            put("ts", System.currentTimeMillis())
        }
        try {
            File(dir, name).writeText(obj.toString(), Charsets.UTF_8)
        } catch (e: Exception) {
            Log.e("SOKLAR-SMS", "No se pudo escribir inbox: ${e.message}")
        }
    }
}