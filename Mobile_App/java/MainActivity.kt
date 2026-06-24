package com.example.projectfalldetecation

import android.Manifest
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.media.AudioManager
import android.net.Uri
import android.os.Bundle
import android.speech.tts.TextToSpeech
import android.telephony.SmsManager
import android.util.Log
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import com.google.firebase.database.DataSnapshot
import com.google.firebase.database.DatabaseError
import com.google.firebase.database.FirebaseDatabase
import com.google.firebase.database.ValueEventListener
import java.text.SimpleDateFormat
import java.util.*

class MainActivity : ComponentActivity(), TextToSpeech.OnInitListener {
    private val caregiverNumber = "01010268636 "
    private val PERMISSION_REQUEST_CODE = 123
    private val TAG = "FALL_DETECTION_DEBUG"
    private var tts: TextToSpeech? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        tts = TextToSpeech(this, this)
        checkPermissions()

        setContent {
            var statusText by remember { mutableStateOf("نظام الطوارئ نشط 🛡️") }
            var subText by remember { mutableStateOf("في انتظار إشارة من الكاميرا...") }

            MaterialTheme {
                Surface(modifier = Modifier.fillMaxSize(), color = MaterialTheme.colorScheme.background) {
                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.Center,
                        modifier = Modifier.padding(16.dp)
                    ) {
                        Text(text = statusText, style = MaterialTheme.typography.headlineMedium)
                        Spacer(modifier = Modifier.height(10.dp))
                        Text(text = subText, style = MaterialTheme.typography.bodyLarge)
                    }
                }
            }

            // --- الجزء الخاص بمراقبة Firebase ---
            LaunchedEffect(Unit) {
                try {
                    // الرابط المباشر لسيرفر بلجيكا لضمان الاتصال
                    val dbUrl = "https://falldetection-4f6fe-default-rtdb.europe-west1.firebasedatabase.app"
                    val database = FirebaseDatabase.getInstance(dbUrl).getReference("fall")

                    database.addValueEventListener(object : ValueEventListener {
                        override fun onDataChange(snapshot: DataSnapshot) {
                            val isDetected = snapshot.child("isDetected").getValue(Boolean::class.java) ?: false
                            Log.d(TAG, "قيمة الفايربيز الحالية: $isDetected")

                            if (isDetected) {
                                Log.d(TAG, "🚨 إشارة سقوط حقيقية! جاري التنفيذ...")
                                statusText = "🚨 تم اكتشاف سقوط!"
                                subText = "جاري الاتصال وإرسال الاستغاثة..."

                                // تشغيل نظام الطوارئ
                                onFallDetected()

                                // تصفير الحالة في Firebase فوراً لمنع التكرار
                                database.child("isDetected").setValue(false)
                            }
                        }

                        override fun onCancelled(error: DatabaseError) {
                            Log.e(TAG, "خطأ في الاتصال بـ Firebase: ${error.message}")
                        }
                    })
                } catch (e: Exception) {
                    Log.e(TAG, "Error initializing Firebase: ${e.message}")
                }
            }
        }
    }

    override fun onInit(status: Int) {
        if (status == TextToSpeech.SUCCESS) {
            tts?.language = Locale.US
        }
    }

    private fun onFallDetected() {
        enableSpeaker()
        sendSmsAndCall(caregiverNumber)
        android.os.Handler(android.os.Looper.getMainLooper()).postDelayed({
            repeatSpeaking(5)
        }, 5000)
    }

    private fun repeatSpeaking(times: Int) {
        if (times > 0 && tts != null) {
            val text = "Emergency. A fall has been detected. Please help."
            tts?.speak(text, TextToSpeech.QUEUE_FLUSH, null, "EmergencyID")
            android.os.Handler(android.os.Looper.getMainLooper()).postDelayed({
                repeatSpeaking(times - 1)
            }, 7000)
        }
    }

    private fun enableSpeaker() {
        try {
            val audioManager = getSystemService(Context.AUDIO_SERVICE) as AudioManager
            audioManager.mode = AudioManager.MODE_IN_CALL
            audioManager.isSpeakerphoneOn = true
            val maxVol = audioManager.getStreamMaxVolume(AudioManager.STREAM_VOICE_CALL)
            audioManager.setStreamVolume(AudioManager.STREAM_VOICE_CALL, maxVol, 0)
        } catch (e: Exception) {
            Log.e(TAG, "Speaker Error: ${e.message}")
        }
    }

    private fun sendSmsAndCall(phoneNumber: String) {
        val hasSms = ContextCompat.checkSelfPermission(this, Manifest.permission.SEND_SMS) == PackageManager.PERMISSION_GRANTED
        val hasCall = ContextCompat.checkSelfPermission(this, Manifest.permission.CALL_PHONE) == PackageManager.PERMISSION_GRANTED

        if (hasSms && hasCall) {
            try {
                val smsManager: SmsManager = SmsManager.getDefault()
                val time = SimpleDateFormat("HH:mm:ss", Locale.getDefault()).format(Date())
                val msg = "🚨 استغاثة سقوط! تم اكتشاف حالة سقوط الآن. الوقت: $time"

                smsManager.sendTextMessage(phoneNumber, null, msg, null, null)
                Log.d(TAG, "SMS Sent!")

                val callIntent = Intent(Intent.ACTION_CALL)
                callIntent.data = Uri.fromParts("tel", phoneNumber, null)
                callIntent.flags = Intent.FLAG_ACTIVITY_NEW_TASK
                startActivity(callIntent)

            } catch (e: Exception) {
                Log.e(TAG, "Call/SMS Error: ${e.localizedMessage}")
                openDialerFallback(phoneNumber)
            }
        } else {
            checkPermissions()
        }
    }

    private fun openDialerFallback(phoneNumber: String) {
        val dialIntent = Intent(Intent.ACTION_DIAL, Uri.fromParts("tel", phoneNumber, null))
        startActivity(dialIntent)
    }

    private fun checkPermissions() {
        val permissions = arrayOf(
            Manifest.permission.SEND_SMS,
            Manifest.permission.CALL_PHONE,
            Manifest.permission.MODIFY_AUDIO_SETTINGS
        )
        val missing = permissions.filter {
            ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED
        }
        if (missing.isNotEmpty()) {
            ActivityCompat.requestPermissions(this, missing.toTypedArray(), PERMISSION_REQUEST_CODE)
        }
    }

    override fun onDestroy() {
        tts?.stop()
        tts?.shutdown()
        super.onDestroy()
    }
}