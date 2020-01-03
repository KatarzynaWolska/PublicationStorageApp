import javafx.event.ActionEvent;
import javafx.fxml.FXMLLoader;
import javafx.scene.Scene;
import javafx.scene.layout.StackPane;
import javafx.stage.Stage;
import org.apache.http.config.RegistryBuilder;
import org.apache.http.conn.socket.ConnectionSocketFactory;
import org.apache.http.conn.socket.PlainConnectionSocketFactory;
import org.apache.http.conn.ssl.NoopHostnameVerifier;
import org.apache.http.conn.ssl.SSLConnectionSocketFactory;
import org.apache.http.impl.client.CloseableHttpClient;
import org.apache.http.impl.client.HttpClientBuilder;
import org.apache.http.impl.conn.PoolingHttpClientConnectionManager;
import org.apache.http.ssl.SSLContextBuilder;

import javax.net.ssl.SSLContext;


public class Utils {
    public CloseableHttpClient httpClient;
    public String baseURL = "https://api.company.com:443";


    public Utils() {
        try {
            final SSLContext sslContext = new SSLContextBuilder()
                    .loadTrustMaterial(null, (x509CertChain, authType) -> true)
                    .build();

            httpClient = HttpClientBuilder.create()
                    .setSSLContext(sslContext)
                    .setConnectionManager(
                            new PoolingHttpClientConnectionManager(
                                    RegistryBuilder.<ConnectionSocketFactory>create()
                                            .register("http", PlainConnectionSocketFactory.INSTANCE)
                                            .register("https", new SSLConnectionSocketFactory(sslContext,
                                                    NoopHostnameVerifier.INSTANCE))
                                            .build()
                            ))
                    .build();

        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public void switchView(FXMLLoader loader, Stage stage) {
        try {
            StackPane stackPane = loader.load();
            Scene scene = new Scene(stackPane, 735, 600);
            stage.setScene(scene);
            stage.show();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

}
