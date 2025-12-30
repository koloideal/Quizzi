from dishka import Provider, Scope


class DatabaseProvider(Provider):
    scope = Scope.APP


class InfrastructureProvider(Provider):
    scope = Scope.APP
