import javafx.application.Platform;
import javafx.event.ActionEvent;
import javafx.fxml.FXML;
import javafx.fxml.FXMLLoader;
import javafx.geometry.Insets;
import javafx.geometry.Pos;
import javafx.scene.Node;
import javafx.scene.control.Alert;
import javafx.scene.control.Button;
import javafx.scene.control.Label;
import javafx.scene.control.TextField;
import javafx.scene.layout.HBox;
import javafx.scene.layout.VBox;
import javafx.stage.FileChooser;
import javafx.stage.Stage;
import org.apache.http.HttpEntity;
import org.apache.http.HttpResponse;
import org.apache.http.client.methods.HttpDelete;
import org.apache.http.client.methods.HttpGet;
import org.apache.http.client.methods.HttpPost;
import org.apache.http.entity.mime.MultipartEntityBuilder;
import org.apache.http.entity.mime.content.FileBody;
import org.apache.http.impl.client.CloseableHttpClient;
import org.apache.http.message.BasicHeader;
import org.apache.http.util.EntityUtils;
import org.json.JSONObject;

import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.net.URL;
import java.nio.channels.Channels;
import java.nio.channels.ReadableByteChannel;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;

public class PublicationWindowController {

    @FXML
    private VBox VBoxPublication;

    @FXML
    private Label titleLabel;

    @FXML
    private Label authorsLabel;

    @FXML
    private Label yearLabel;

    @FXML
    private Label publisherLabel;

    @FXML
    private TextField filePathTextField;

    @FXML
    private Button sendFileButton;

    @FXML
    private Button chooseFileButton;

    @FXML
    private VBox filesVBox;


    private String token;
    private JSONObject pubInfoJSON;
    private JSONObject pubFilesJSON;

    private CloseableHttpClient httpClient;
    private Utils utils;

    private String URL_getUpdateDeletePub;
    private String URL_getAddPublications;
    private String URL_uploadGetFiles;

    private Map fileTitleToID;
    private Map linksDownloadDeleteFile;

    @FXML
    public void initialize() {
        try {
            getPublication();
            if (pubInfoJSON != null) {
                String pubInfo = pubInfoJSON.get("publication").toString();
                JSONObject publicationInfo = new JSONObject(pubInfo);
                titleLabel.setText(publicationInfo.get("title").toString());
                authorsLabel.setText(publicationInfo.get("authors").toString());
                yearLabel.setText(publicationInfo.get("year").toString());
                publisherLabel.setText(publicationInfo.get("publisher").toString());

                if (pubFilesJSON != null) {
                    String files = pubFilesJSON.get("files").toString();
                    JSONObject filesInfo = new JSONObject(files);

                    Iterator<String> keys = filesInfo.keys();

                    while (keys.hasNext()) {
                        String key = keys.next();
                        fileTitleToID.put(filesInfo.get(key).toString(), key);

                        HBox fileHBox = new HBox();
                        fileHBox.setAlignment(Pos.CENTER);
                        fileHBox.setId(key);
                        fileHBox.getChildren().add(new Label(filesInfo.get(key).toString()));
                        Button downloadFileBtn = new Button("Download file");
                        downloadFileBtn.setOnAction(this::clickOnDownload);
                        fileHBox.getChildren().add(downloadFileBtn);
                        Button deleteFileBtn = new Button("Delete file");
                        deleteFileBtn.setOnAction(this::clickOnDelete);
                        fileHBox.getChildren().add(deleteFileBtn);

                        fileHBox.paddingProperty().setValue(new Insets(0, 0, 10, 0));
                        HBox.setMargin(downloadFileBtn, new Insets(0, 30, 0, 30));

                        filesVBox.getChildren().add(fileHBox);
                    }

                    String links = pubFilesJSON.get("_links").toString();
                    JSONObject linksJSON = new JSONObject(links);

                    keys = linksJSON.keys();

                    while (keys.hasNext()) {
                        String key = keys.next();

                        if (!key.equals("self")) {
                            String linkJSONStr = linksJSON.get(key).toString();
                            JSONObject linkJSON = new JSONObject(linkJSONStr);

                            String path = new URL(linkJSON.get("href").toString()).getPath();
                            String requestURL = utils.baseURL + path;

                            if (linkJSON.get("name").toString().equals("download_or_delete_file")) {
                                linksDownloadDeleteFile.put(key, requestURL);
                            }
                        }
                    }
                }
            }

        } catch (Exception e) {
            e.printStackTrace();
        }

    }

    public PublicationWindowController(String URL_getUpdateDeletePub, String uploadFiles, String URL_getPublications, String token) {
        this.token = token;
        this.URL_getUpdateDeletePub = URL_getUpdateDeletePub;
        this.URL_getAddPublications = URL_getPublications;
        this.URL_uploadGetFiles = uploadFiles;
        this.fileTitleToID = new HashMap<String, String>();
        this.linksDownloadDeleteFile = new HashMap<String, String>();
        utils = new Utils();
        httpClient = utils.httpClient;
    }

    public void clickOnSendFile(ActionEvent actionEvent) {
        try {
            String filePath = filePathTextField.getText();
            File file = new File(filePath);

            if (file.exists() && !file.isDirectory()) {
                HttpEntity entity = MultipartEntityBuilder.create()
                        .addPart("file", new FileBody(file))
                        .build();

                HttpPost request = new HttpPost(URL_uploadGetFiles);
                request.setHeader(new BasicHeader("Authorization", token));
                request.setEntity(entity);
                HttpResponse response = httpClient.execute(request);

                String json = EntityUtils.toString(response.getEntity());
                JSONObject responseJSON = new JSONObject(json);

                if (response.getStatusLine().getStatusCode() == 201) {
                    String links = responseJSON.get("_links").toString();
                    JSONObject linksJSON = new JSONObject(links);

                    Iterator<String> keys = linksJSON.keys();;

                    while (keys.hasNext()) {
                        String key = keys.next();

                        if (linksDownloadDeleteFile.get(key) == null && !key.equals("self")) {
                            String linkStr = linksJSON.get(key).toString();
                            JSONObject linkJSON = new JSONObject(linkStr);
                            if (linkJSON.get("name").toString().equals("download_or_delete_file")) {
                                String path = new URL(linkJSON.get("href").toString()).getPath();
                                String requestURL = utils.baseURL + path;
                                linksDownloadDeleteFile.put(key, requestURL);
                            }
                            fileTitleToID.put(file.getName(), key);

                            HBox fileHBox = new HBox();
                            fileHBox.setAlignment(Pos.CENTER);
                            fileHBox.setId(key);
                            fileHBox.getChildren().add(new Label(file.getName()));
                            Button downloadFileBtn = new Button("Download file");
                            downloadFileBtn.setOnAction(this::clickOnDownload);
                            fileHBox.getChildren().add(downloadFileBtn);
                            Button deleteFileBtn = new Button("Delete file");
                            deleteFileBtn.setOnAction(this::clickOnDelete);
                            fileHBox.getChildren().add(deleteFileBtn);

                            HBox.setMargin(downloadFileBtn, new Insets(0, 30, 0, 30));
                            fileHBox.paddingProperty().setValue(new Insets(0, 0, 10, 0));

                            filesVBox.getChildren().add(fileHBox);
                        }
                    }

                } else {
                    Alert alert = new Alert(Alert.AlertType.INFORMATION);
                    alert.setTitle("Error");
                    alert.setHeaderText(responseJSON.get("message").toString());
                    alert.showAndWait();

                    if (response.getStatusLine().getStatusCode() == 401) {
                        switchViewToLogin();
                    }
                }
            }

        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public void backToPublications(ActionEvent actionEvent) {
        PublicationsWindowController controller = new PublicationsWindowController(this.URL_getAddPublications, token);
        FXMLLoader loader = new FXMLLoader(getClass().getResource("publicationsWindow.fxml"));
        Stage stage = (Stage) titleLabel.getParent().getScene().getWindow();
        loader.setController(controller);
        utils.switchView(loader, stage);
    }

    public void clickOnChooseFile(ActionEvent actionEvent) {
        FileChooser fileChooser = new FileChooser();
        Stage mainStage = (Stage) titleLabel.getScene().getWindow();
        File selectedFile = fileChooser.showOpenDialog(mainStage);
        if (selectedFile != null) {
            String path = selectedFile.getAbsolutePath();
            filePathTextField.setText(path);
        }
    }

    public void clickOnUpdatePublication(ActionEvent actionEvent) {
        try {
            String pubInfo = pubInfoJSON.get("publication").toString();
            JSONObject publicationInfo = new JSONObject(pubInfo);

            UpdatePublicationWindowController controller = new UpdatePublicationWindowController(publicationInfo, URL_getUpdateDeletePub, URL_getAddPublications, URL_uploadGetFiles, token);
            FXMLLoader loader = new FXMLLoader(getClass().getResource("updatePublicationWindow.fxml"));
            Stage stage = (Stage) titleLabel.getParent().getScene().getWindow();
            loader.setController(controller);
            utils.switchView(loader, stage);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public void clickOnDeletePublication(ActionEvent actionEvent) {
        try {
            HttpDelete request = new HttpDelete(URL_getUpdateDeletePub);
            request.setHeader(new BasicHeader("Authorization", token));
            HttpResponse response = httpClient.execute(request);

            String json = EntityUtils.toString(response.getEntity());
            JSONObject responseJSON = new JSONObject(json);

            if (response.getStatusLine().getStatusCode() == 200) {
                Alert alert = new Alert(Alert.AlertType.INFORMATION);
                alert.setTitle(responseJSON.get("message").toString());
                alert.setHeaderText(responseJSON.get("message").toString());
                alert.showAndWait();

                PublicationsWindowController controller = new PublicationsWindowController(URL_getAddPublications, token);
                FXMLLoader loader = new FXMLLoader(getClass().getResource("publicationsWindow.fxml"));
                Stage stage = (Stage) titleLabel.getParent().getScene().getWindow();
                loader.setController(controller);
                utils.switchView(loader, stage);
            } else {
                Alert alert = new Alert(Alert.AlertType.INFORMATION);
                alert.setTitle("Error");
                alert.setHeaderText(responseJSON.get("message").toString());
                alert.showAndWait();

                if (response.getStatusLine().getStatusCode() == 401) {
                    switchViewToLogin();
                }
            }

        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public void clickOnDownload(ActionEvent actionEvent) {
        Button buttonClicked = (Button)actionEvent.getSource();
        String fileID = buttonClicked.getParent().getId();

        String URL_downloadFile = linksDownloadDeleteFile.get(fileID).toString();

        try {
            HttpGet request = new HttpGet(URL_downloadFile);
            request.setHeader(new BasicHeader("Authorization", token));
            HttpResponse response = httpClient.execute(request);

            if (response.getStatusLine().getStatusCode() == 200) {
                HttpEntity entity = response.getEntity();
                InputStream instream = entity.getContent();
                ReadableByteChannel rbc = Channels.newChannel(instream);

                String fileName = "";

                for (Object key : fileTitleToID.keySet()) {
                    if (fileTitleToID.get(key).equals(fileID)) {
                        fileName = key.toString();
                    }
                }

                FileOutputStream fos = new FileOutputStream(fileName);
                fos.getChannel().transferFrom(rbc, 0, Long.MAX_VALUE);

                Alert alert = new Alert(Alert.AlertType.INFORMATION);
                alert.setTitle("File downloaded");
                alert.setHeaderText("File downloaded");
                alert.showAndWait();
            } else {
                String json = EntityUtils.toString(response.getEntity());
                JSONObject responseJSON = new JSONObject(json);

                Alert alert = new Alert(Alert.AlertType.INFORMATION);
                alert.setTitle("Error");
                alert.setHeaderText(responseJSON.get("message").toString());
                alert.showAndWait();

                if (response.getStatusLine().getStatusCode() == 401) {
                    switchViewToLogin();
                }
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public void clickOnDelete(ActionEvent actionEvent) {
        Button buttonClicked = (Button)actionEvent.getSource();
        String fileID = buttonClicked.getParent().getId();

        String URL_deleteFile = linksDownloadDeleteFile.get(fileID).toString();

        try {
            HttpDelete request = new HttpDelete(URL_deleteFile);
            request.setHeader(new BasicHeader("Authorization", token));
            HttpResponse response = httpClient.execute(request);

            String json = EntityUtils.toString(response.getEntity());
            JSONObject responseJSON = new JSONObject(json);

            if (response.getStatusLine().getStatusCode() == 200) {
                Alert alert = new Alert(Alert.AlertType.INFORMATION);
                alert.setTitle("File deleted");
                alert.setHeaderText("File deleted");
                alert.showAndWait();

                Node nodeToRemove = null;
                for (Node n : filesVBox.getChildren()) {
                    if (n.getId() != null && n.getId().equals(fileID)) {
                        nodeToRemove = n;
                    }
                }
                filesVBox.getChildren().remove(nodeToRemove);
            } else {
                Alert alert = new Alert(Alert.AlertType.INFORMATION);
                alert.setTitle("Error");
                alert.setHeaderText(responseJSON.get("message").toString());
                alert.showAndWait();

                if (response.getStatusLine().getStatusCode() == 401) {
                    switchViewToLogin();
                }
            }

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
            Stage stage = (Stage) titleLabel.getParent().getScene().getWindow();
            utils.switchView(loader, stage);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private void getPublication() {
        try {
            HttpGet request = new HttpGet(URL_getUpdateDeletePub);
            request.setHeader(new BasicHeader("Authorization", token));
            HttpResponse response = httpClient.execute(request);

            String json = EntityUtils.toString(response.getEntity());
            JSONObject pubInfoJSON = new JSONObject(json);

            if (response.getStatusLine().getStatusCode() == 200) {
                this.pubInfoJSON = pubInfoJSON;
            } else {
                Alert alert = new Alert(Alert.AlertType.INFORMATION);
                alert.setTitle("Error");
                alert.setHeaderText(pubInfoJSON.get("message").toString());
                alert.showAndWait();

                if (response.getStatusLine().getStatusCode() == 401) {
                    Platform.runLater(() -> switchViewToLogin());
                }
            }

            request = new HttpGet(this.URL_uploadGetFiles);
            request.setHeader(new BasicHeader("Authorization", token));
            response = httpClient.execute(request);

            json = EntityUtils.toString(response.getEntity());
            JSONObject pubFilesJSON = new JSONObject(json);

            if (response.getStatusLine().getStatusCode() == 200) {
                this.pubFilesJSON = pubFilesJSON;
            } else {
                Alert alert = new Alert(Alert.AlertType.INFORMATION);
                alert.setTitle("Error");
                alert.setHeaderText(pubFilesJSON.get("message").toString());
                alert.showAndWait();

                if (response.getStatusLine().getStatusCode() == 401) {
                    switchViewToLogin();
                }
            }

        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
