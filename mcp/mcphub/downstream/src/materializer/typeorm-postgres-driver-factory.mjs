import { MissingDriverError } from "typeorm/error/MissingDriverError.js";
import { PostgresDriver } from "typeorm/driver/postgres/PostgresDriver.js";

export class DriverFactory {
  create(connection) {
    if (connection.options.type !== "postgres") {
      throw new MissingDriverError(connection.options.type, ["postgres"]);
    }
    return new PostgresDriver(connection);
  }
}
