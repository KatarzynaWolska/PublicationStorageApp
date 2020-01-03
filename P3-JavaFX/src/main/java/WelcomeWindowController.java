import javafx.event.ActionEvent;
import javafx.fxml.FXML;
import javafx.fxml.FXMLLoader;
import javafx.scene.control.Button;
import javafx.scene.control.Label;
import javafx.stage.Stage;
import org.apache.http.impl.client.CloseableHttpClient;
import java.net.URL;


public class WelcomeWindowController {
    // PODODAWAC ZEBY NIE WYSYLALO FORMY NIE WYPELNIONEJ

    @FXML
    private Label welcomeLabel;

    @FXML
    private Button logOutBtn;

    private String token;
    private String username;
    private String getAddPublicationsURL;
    private CloseableHttpClient httpClient;
    private Utils utils;

    @FXML
    public void initialize() {
        welcomeLabel.setText("Welcome " + username + "!");
        logOutBtn.setOnAction(this::logOut);
    }

    public WelcomeWindowController(String username, String token, String getAddPublicationURL) {
        this.username = username;
        this.token = token;
        this.getAddPublicationsURL = getAddPublicationURL;
        utils = new Utils();
        httpClient = utils.httpClient;
    }


    public void myPublications(ActionEvent actionEvent) {
        try {
            String path = new URL(this.getAddPublicationsURL).getPath();
            String requestURL = utils.baseURL + path;
            this.getAddPublicationsURL = requestURL;

            PublicationsWindowController controller = new PublicationsWindowController(getAddPublicationsURL, token);
            FXMLLoader loader = new FXMLLoader(getClass().getResource("publicationsWindow.fxml"));
            Stage stage = (Stage) welcomeLabel.getParent().getScene().getWindow();
            loader.setController(controller);
            utils.switchView(loader, stage);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public void logOut(ActionEvent actionEvent) {
        switchViewToLogin();
    }

    private void switchViewToLogin() {
        try {
            FXMLLoader loader = new FXMLLoader(getClass().getResource("loginWindow.fxml"));
            Stage stage = (Stage) welcomeLabel.getParent().getScene().getWindow();
            utils.switchView(loader, stage);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
