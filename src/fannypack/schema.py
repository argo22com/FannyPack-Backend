import graphene
import graphql_jwt

import payments.schema


class Query(payments.schema.Query, graphene.ObjectType):
    pass


class Mutation(payments.schema.Mutation, graphene.ObjectType):
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()


schema = graphene.Schema(query=Query, mutation= Mutation)
