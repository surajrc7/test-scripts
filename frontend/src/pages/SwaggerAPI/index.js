import { useEffect } from 'react'
import SwaggerUI from "swagger-ui-react";

import "swagger-ui-react/swagger-ui.css";

export default function SwaggerApi() {

    return (
        <div className="App">
          <SwaggerUI url="http://0.0.0.0:8080/doc/?format=openapi"  defaultModelsExpandDepth="-1"/>
        </div>
      );

}
