import { Amplify, Auth } from "aws-amplify";
import { useCallback, useEffect } from "react";
import App from "./App";
import awsconfig from "./aws-exports";
import { userNameFromEmail } from "./utils/helpers";
import { useUserStore } from "./+state/UserSlice";
import { Spin } from "antd";

Amplify.configure(awsconfig);

export default function SecureApp() {
  const { userData, setUserData } = useUserStore();

  const authenticateUser = useCallback(() => {
    Auth.currentAuthenticatedUser({ bypassCache: true })
      .then((user) => {
        const res = user.signInUserSession;
        const idToken: string = res.getIdToken().getJwtToken() as string;
        const userId: string = res.getIdToken().payload.sub as string;
        const userEmail: string = res.getIdToken().payload.email as string;
        const userName: string = userNameFromEmail(userEmail) as string;
        const accessToken: string = res
          .getAccessToken()
          .getJwtToken() as string; // Assuming groups are in access token.

        // Decode the access token to get the payload
        const payload = JSON.parse(atob(accessToken.split(".")[1])); // Decode base64 token payload
        const groups = payload["cognito:groups"] || []; // Replace 'cognito:groups' with the correct claim key if different
        setUserData({
          id: userId,
          email: userEmail,
          name: userName,
          idToken,
          groups,
          accessToken,
        });
      })
      .catch((_e) => {
        setUserData(null);
        // Federated-sign-in redirects to Okta and then back - after calling it, authenticateUser function is called again
        Auth.federatedSignIn({
          customProvider: "Okta",
        });
      });
  }, []);

  useEffect(() => {
    authenticateUser();
  }, [authenticateUser]);

  return (
    <>
      {userData ? (
        <App />
      ) : (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            height: "100%",
          }}
        >
          <Spin size="large" style={{ fontSize: "1.5rem" }} />
        </div>
      )}
    </>
  );
}
