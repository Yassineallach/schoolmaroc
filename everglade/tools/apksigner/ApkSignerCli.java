// Minimal `apksigner` replacement built on Google's apksig library.
// Implements just what Godot's Android exporter calls:
//   apksigner --version
//   apksigner sign [--verbose] --ks <keystore> --ks-pass pass:<pw> --ks-key-alias <alias> <apk>
//   apksigner verify [--verbose] <apk>
// Only needed when the official Android SDK build-tools are unavailable.
import com.android.apksig.ApkSigner;
import com.android.apksig.ApkVerifier;
import java.io.File;
import java.io.FileInputStream;
import java.nio.file.Files;
import java.nio.file.StandardCopyOption;
import java.security.KeyStore;
import java.security.PrivateKey;
import java.security.cert.X509Certificate;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public class ApkSignerCli {
    public static void main(String[] args) throws Exception {
        if (args.length == 0 || args[0].equals("--version") || args[0].equals("version")) {
            System.out.println("0.9 (apksig 2.3.0)");
            return;
        }
        String cmd = args[0];
        String ks = null, pass = "", alias = null, apk = null;
        for (int i = 1; i < args.length; i++) {
            switch (args[i]) {
                case "--verbose": break;
                case "--ks": ks = args[++i]; break;
                case "--ks-pass": pass = args[++i].replaceFirst("^pass:", ""); break;
                case "--ks-key-alias": alias = args[++i]; break;
                default: apk = args[i];
            }
        }
        if (apk == null) { System.err.println("No APK given"); System.exit(2); }
        if (cmd.equals("verify")) {
            ApkVerifier.Result r = new ApkVerifier.Builder(new File(apk)).build().verify();
            System.out.println("Verifies: " + r.isVerified() + " (v1=" + r.isVerifiedUsingV1Scheme() + ", v2=" + r.isVerifiedUsingV2Scheme() + ")");
            for (ApkVerifier.IssueWithParams e : r.getErrors()) System.err.println("ERROR: " + e);
            System.exit(r.isVerified() ? 0 : 1);
        }
        if (!cmd.equals("sign")) { System.err.println("Unknown command " + cmd); System.exit(2); }
        KeyStore store = KeyStore.getInstance(ks.endsWith(".p12") ? "PKCS12" : KeyStore.getDefaultType());
        try (FileInputStream in = new FileInputStream(ks)) { store.load(in, pass.toCharArray()); }
        if (alias == null) alias = Collections.list(store.aliases()).get(0);
        PrivateKey key = (PrivateKey) store.getKey(alias, pass.toCharArray());
        List<X509Certificate> certs = new ArrayList<>();
        for (java.security.cert.Certificate c : store.getCertificateChain(alias)) certs.add((X509Certificate) c);
        ApkSigner.SignerConfig cfg = new ApkSigner.SignerConfig.Builder("CERT", key, certs).build();
        File in = new File(apk);
        File out = new File(apk + ".signed.tmp");
        new ApkSigner.Builder(Collections.singletonList(cfg))
                .setInputApk(in).setOutputApk(out)
                .setMinSdkVersion(24) // Godot 4.7 min SDK; v2 scheme is enough
                .setV1SigningEnabled(false).setV2SigningEnabled(true)
                .build().sign();
        Files.move(out.toPath(), in.toPath(), StandardCopyOption.REPLACE_EXISTING);
        System.out.println("Signed");
    }
}
